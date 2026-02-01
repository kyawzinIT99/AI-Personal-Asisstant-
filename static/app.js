// Tab Switching
function showSection(sectionId) {
    // Hide all sections
    document.getElementById('mail-section').style.display = 'none';
    document.getElementById('calendar-section').style.display = 'none';
    document.getElementById('leads-section').style.display = 'none';

    // Deselect menu items
    document.querySelectorAll('.sidebar li').forEach(li => li.classList.remove('active'));

    // Show target section
    document.getElementById(sectionId + '-section').style.display = 'block';

    // Select menu item
    const menuItems = document.querySelectorAll('.sidebar li');
    if (sectionId === 'mail') menuItems[0].classList.add('active');
    if (sectionId === 'calendar') menuItems[1].classList.add('active');
    if (sectionId === 'leads') menuItems[2].classList.add('active');

    // Auto load data
    if (sectionId === 'mail') fetchMail();
    if (sectionId === 'calendar') fetchCalendar();

    // Update active class for new items
    if (sectionId === 'web') menuItems[3].classList.add('active');
    if (sectionId === 'chat') menuItems[4].classList.add('active');
    if (sectionId === 'weather') menuItems[5].classList.add('active');
    if (sectionId === 'blog') menuItems[6].classList.add('active');
    if (sectionId === 'image') menuItems[7].classList.add('active');
    if (sectionId === 'image-search') menuItems[8].classList.add('active');
}

// Format Date Utility
function formatDate(isoString) {
    if (!isoString) return '';
    return new Date(isoString).toLocaleString();
}

// --- MAIL LOGIC ---

// Email State
let currentMessageId = null;

async function fetchMail() {
    const listContainer = document.getElementById('mail-list');
    listContainer.innerHTML = '<div class="loading">Loading emails...</div>';

    try {
        const response = await fetch('/api/mail/list?max_results=10');
        const data = await response.json();

        if (data.status === 'success') {
            listContainer.innerHTML = '';
            data.messages.forEach(msg => {
                const item = document.createElement('div');
                item.className = 'list-item';
                item.onclick = () => viewEmail(msg.id); // Add click handler
                item.innerHTML = `
                    <div class="list-item-title">${msg.subject}</div>
                    <div class="list-item-subtitle">From: ${msg.from}</div>
                    <div class="list-item-snippet">${msg.snippet}</div>
                `;
                listContainer.appendChild(item);
            });
        } else {
            listContainer.innerHTML = `<div class="loading">Error: ${data.message}</div>`;
        }
    } catch (error) {
        listContainer.innerHTML = `<div class="loading">Error loading mails: ${error}</div>`;
    }
}

async function viewEmail(id) {
    currentMessageId = id;
    document.getElementById('mail-list-card').style.display = 'none';
    document.getElementById('compose-card').style.display = 'none';
    const detailCard = document.getElementById('mail-detail-card');
    detailCard.style.display = 'block';

    // Clear previous content
    document.getElementById('detail-subject').innerText = 'Loading...';
    document.getElementById('detail-body').innerText = '';

    try {
        const response = await fetch(`/api/mail/read/${id}`);
        const data = await response.json();

        if (data.status === 'success') {
            document.getElementById('detail-subject').innerText = data.subject;
            document.getElementById('detail-from').innerText = `From: ${data.from}`;
            document.getElementById('detail-body').innerText = data.body || '(No content)';
        } else {
            alert('Error loading email: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error);
    }
}

function closeMailDetail() {
    document.getElementById('mail-detail-card').style.display = 'none';
    document.getElementById('mail-list-card').style.display = 'block';
    document.getElementById('compose-card').style.display = 'block';
    currentMessageId = null;
}

// Send Email (Normal)
document.getElementById('mail-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerText;
    btn.innerText = 'Sending...';
    btn.disabled = true;

    const payload = {
        to: document.getElementById('mail-to').value,
        subject: document.getElementById('mail-subject').value,
        body: document.getElementById('mail-body').value
    };

    try {
        const response = await fetch('/api/mail/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('Email sent successfully!');
            e.target.reset();
            fetchMail(); // Refresh list
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// Save Draft
document.getElementById('btn-save-draft').addEventListener('click', async () => {
    const btn = document.getElementById('btn-save-draft');
    const originalText = btn.innerText;
    btn.innerText = 'Saving...';
    btn.disabled = true;

    const payload = {
        to: document.getElementById('mail-to').value,
        subject: document.getElementById('mail-subject').value,
        body: document.getElementById('mail-body').value
    };

    try {
        const response = await fetch('/api/mail/draft', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('Draft saved successfully!');
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// Reply
async function sendReply() {
    if (!currentMessageId) return;

    const body = document.getElementById('reply-body').value;
    if (!body) {
        alert('Please enter a reply message');
        return;
    }

    try {
        const response = await fetch('/api/mail/reply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_id: currentMessageId,
                body: body
            })
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('Reply sent successfully!');
            document.getElementById('reply-body').value = '';
            closeMailDetail();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Network error: ' + error);
    }
}

// Delete
async function deleteCurrentEmail() {
    if (!currentMessageId) return;

    if (!confirm('Are you sure you want to delete this email?')) return;

    try {
        const response = await fetch(`/api/mail/delete/${currentMessageId}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('Email deleted (moved to Trash).');
            closeMailDetail();
            fetchMail();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Network error: ' + error);
    }
}

// --- CALENDAR LOGIC ---

let currentEventId = null;

async function fetchCalendar() {
    const listContainer = document.getElementById('event-list');
    listContainer.innerHTML = '<div class="loading">Loading events...</div>';

    try {
        const response = await fetch('/api/calendar/list?max_results=10');
        const data = await response.json();

        if (data.status === 'success') {
            listContainer.innerHTML = '';
            data.events.forEach(evt => {
                const item = document.createElement('div');
                item.className = 'list-item';
                item.onclick = () => viewEvent(evt.id); // Click to view details

                const timeStr = evt.start.includes('T')
                    ? formatDate(evt.start)
                    : evt.start + ' (All Day)';

                item.innerHTML = `
                    <div class="list-item-title">${evt.summary}</div>
                    <div class="list-item-subtitle">${timeStr}</div>
                `;
                listContainer.appendChild(item);
            });
        } else {
            listContainer.innerHTML = `<div class="loading">Error: ${data.message}</div>`;
        }
    } catch (error) {
        listContainer.innerHTML = `<div class="loading">Error loading events: ${error}</div>`;
    }
}

async function viewEvent(id) {
    currentEventId = id;
    document.getElementById('calendar-list-card').style.display = 'none';
    document.getElementById('calendar-create-card').style.display = 'none';
    const detailCard = document.getElementById('calendar-detail-card');
    detailCard.style.display = 'block';

    // Reset form
    document.getElementById('calendar-update-form').reset();

    try {
        const response = await fetch(`/api/calendar/event/${id}`);
        const data = await response.json();

        if (data.status === 'success') {
            document.getElementById('update-event-id').value = data.id;
            document.getElementById('update-event-summary').value = data.summary;
            document.getElementById('update-event-description').value = data.description || '';

            // Format datetime for input (YYYY-MM-DDTHH:MM)
            if (data.start && data.start.includes('T')) {
                document.getElementById('update-event-start').value = data.start.slice(0, 16);
            }

            // Calculate duration if possible, or just leave blank to not auto-update end unless changed
            if (data.start && data.end) {
                const start = new Date(data.start);
                const end = new Date(data.end);
                const diffMinutes = Math.round((end - start) / 60000);
                document.getElementById('update-event-duration').value = diffMinutes;
            }

            if (data.attendees && data.attendees.length > 0) {
                document.getElementById('update-event-attendees').value = data.attendees.join(', ');
            }
        } else {
            alert('Error loading event: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error);
    }
}

function closeEventDetail() {
    document.getElementById('calendar-detail-card').style.display = 'none';
    document.getElementById('calendar-list-card').style.display = 'block';
    document.getElementById('calendar-create-card').style.display = 'block';
    currentEventId = null;
}

document.getElementById('calendar-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Creating...';
    btn.disabled = true;

    const payload = {
        summary: document.getElementById('event-summary').value,
        start_time: document.getElementById('event-start').value,
        duration_minutes: parseInt(document.getElementById('event-duration').value),
        description: document.getElementById('event-description').value,
        attendees: document.getElementById('event-attendees').value
    };

    try {
        const response = await fetch('/api/calendar/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('Event scheduled successfully!');
            e.target.reset();
            fetchCalendar(); // Refresh list
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

document.getElementById('calendar-update-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Updating...';
    btn.disabled = true;

    const payload = {
        event_id: document.getElementById('update-event-id').value,
        summary: document.getElementById('update-event-summary').value,
        start_time: document.getElementById('update-event-start').value,
        duration_minutes: parseInt(document.getElementById('update-event-duration').value),
        description: document.getElementById('update-event-description').value,
        attendees: document.getElementById('update-event-attendees').value
    };

    try {
        const response = await fetch('/api/calendar/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('Event updated successfully!');
            closeEventDetail();
            fetchCalendar();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

async function deleteCurrentEvent() {
    if (!currentEventId) return;
    if (!confirm('Are you sure you want to delete this event?')) return;

    try {
        const response = await fetch(`/api/calendar/delete/${currentEventId}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('Event deleted.');
            closeEventDetail();
            fetchCalendar();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Network error: ' + error);
    }
}

// --- LEADS LOGIC ---

document.getElementById('leads-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Searching...';
    btn.disabled = true;

    const query = document.getElementById('lead-query').value;
    const location = document.getElementById('lead-location').value;
    const mock = document.getElementById('lead-mock').checked;

    const listContainer = document.getElementById('leads-list');
    listContainer.innerHTML = '<div class="loading">Searching leads...</div>';

    try {
        const response = await fetch(`/api/leads/search?query=${encodeURIComponent(query)}&location=${encodeURIComponent(location)}&mock=${mock}&limit=5`);
        const data = await response.json();

        if (data.status === 'success') {
            listContainer.innerHTML = '';
            if (data.leads.length === 0) {
                listContainer.innerHTML = '<div class="placeholder-text">No leads found.</div>';
            } else {
                data.leads.forEach(lead => {
                    const item = document.createElement('div');
                    item.className = 'list-item';
                    item.innerHTML = `
                        <div class="list-item-title">${lead.name} (${lead.jobTitle})</div>
                        <div class="list-item-subtitle">${lead.company} - ${lead.location}</div>
                        <div style="font-size: 0.8em; margin-top: 5px;">
                            ${lead.headline}<br>
                            <a href="${lead.linkedInUrl}" target="_blank" style="color: #a0c4ff;">LinkedIn</a> | 
                            <a href="${lead.companyUrl}" target="_blank" style="color: #a0c4ff;">Company</a>
                        </div>
                    `;
                    listContainer.appendChild(item);
                });
            }
        } else {
            listContainer.innerHTML = `<div class="loading">Error: ${data.message}</div>`;
        }
    } catch (error) {
        listContainer.innerHTML = `<div class="loading">Network Error: ${error}</div>`;
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// --- WEB AGENT LOGIC ---
document.getElementById('web-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Searching...';
    btn.disabled = true;

    const query = document.getElementById('web-query').value;
    const resultsContainer = document.getElementById('web-results');
    document.getElementById('web-results-card').style.display = 'block';
    resultsContainer.innerHTML = '<div class="loading">Searching web...</div>';

    try {
        const response = await fetch('/api/web/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await response.json();

        if (data.results) {
            resultsContainer.innerHTML = '';

            // Show AI Summary if available
            if (data.ai_summary) {
                const summaryDiv = document.createElement('div');
                summaryDiv.className = 'card';
                summaryDiv.style.background = 'rgba(108, 92, 231, 0.1)';
                summaryDiv.style.marginBottom = '20px';
                summaryDiv.innerHTML = `
                    <h3 style="color: var(--accent); margin-bottom: 10px;">✨ AI Summary</h3>
                    <p style="line-height: 1.5;">${data.ai_summary}</p>
                `;
                resultsContainer.appendChild(summaryDiv);
            }

            data.results.forEach(res => {
                const item = document.createElement('div');
                item.className = 'list-item';
                item.innerHTML = `
                    <div class="list-item-title"><a href="${res.url}" target="_blank" style="color: #a0c4ff;">${res.title}</a></div>
                    <div class="list-item-snippet">${res.content}</div>
                `;
                resultsContainer.appendChild(item);
            });
        } else if (data.error) {
            resultsContainer.innerHTML = `<div class="loading">Error: ${data.error}</div>`;
        } else {
            resultsContainer.innerHTML = `<div class="loading">No results found or unexpected format.</div>`;
        }
    } catch (error) {
        resultsContainer.innerHTML = `<div class="loading">Network Error: ${error}</div>`;
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// --- CHAT AGENT LOGIC ---
const chatHistory = []; // Local history for context if needed, though API is stateless usually unless we pass history

document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const message = input.value;
    if (!message) return;

    // Add user message
    addChatMessage(message, 'user');
    input.value = '';

    const btn = e.target.querySelector('button');
    btn.disabled = true;

    // Build messages payload (simple history)
    const messages = [
        { role: "system", content: "You are a helpful AI assistant." },
        ...chatHistory,
        { role: "user", content: message }
    ];

    try {
        const response = await fetch('/api/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: messages })
        });
        const data = await response.json();

        if (data.choices && data.choices.length > 0) {
            const reply = data.choices[0].message.content;
            addChatMessage(reply, 'bot');

            // Update local history
            chatHistory.push({ role: "user", content: message });
            chatHistory.push({ role: "assistant", content: reply });
        } else if (data.error) {
            addChatMessage(`Error: ${data.error}`, 'bot');
        } else {
            addChatMessage("Error: Received empty response.", 'bot');
        }
    } catch (error) {
        addChatMessage(`Network Error: ${error}`, 'bot');
    } finally {
        btn.disabled = false;
    }
});

function addChatMessage(text, sender) {
    const container = document.getElementById('chat-history');
    const div = document.createElement('div');
    div.className = `chat-message ${sender}`;
    div.innerText = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// --- WEATHER AGENT LOGIC ---
document.getElementById('weather-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Loading...';
    btn.disabled = true;

    const city = document.getElementById('weather-city').value;
    const resultDiv = document.getElementById('weather-result');
    resultDiv.style.display = 'none';

    try {
        const response = await fetch(`/api/weather/current?city=${encodeURIComponent(city)}`);
        const data = await response.json();

        if (data.main) {
            resultDiv.style.display = 'block';
            document.getElementById('weather-city-name').innerText = `${data.name}, ${data.sys.country}`;
            document.getElementById('weather-temp').innerText = `${Math.round(data.main.temp)}°C`;
            document.getElementById('weather-desc').innerText = data.weather[0].description;
            document.getElementById('weather-humidity').innerText = `Humidity: ${data.main.humidity}%`;
            document.getElementById('weather-wind').innerText = `Wind: ${data.wind.speed} m/s`;
        } else {
            alert(data.error || 'Error fetching weather data');
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// --- BLOG AGENT LOGIC ---
document.getElementById('blog-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Generating (this may take a minute)...';
    btn.disabled = true;

    const topic = document.getElementById('blog-topic').value;
    const audience = document.getElementById('blog-audience').value;
    const chatId = document.getElementById('blog-chat-id').value;

    const resultDiv = document.getElementById('blog-result');
    resultDiv.style.display = 'none';

    try {
        const response = await fetch('/api/blog/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: topic,
                audience: audience,
                chat_id: chatId
            })
        });
        const data = await response.json();

        if (data.status === 'success') {
            resultDiv.style.display = 'block';
            document.getElementById('blog-image-title').innerText = data.image_title;
            const img = document.getElementById('blog-image');
            img.src = data.image_url;
            img.style.display = 'block';

            // Format blog post with simple HTML line breaks
            document.getElementById('blog-content').innerHTML = marked.parse(data.blog_post); // Assuming marked.js is available or just text
            // If marked.js isn't available, fallback to simple text
            if (typeof marked === 'undefined') {
                document.getElementById('blog-content').innerText = data.blog_post;
            }

            if (data.telegram_status) {
                alert(`Blog generated! Telegram status: ${data.telegram_status}`);
            }
        } else {
            alert('Error: ' + (data.message || data.error));
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// --- IMAGE AGENT LOGIC ---
document.getElementById('image-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Generatiing (approx 30s)...';
    btn.disabled = true;

    const title = document.getElementById('image-title').value;
    const prompt = document.getElementById('image-prompt').value;
    const chatId = document.getElementById('image-chat-id').value;

    const resultDiv = document.getElementById('image-result');
    resultDiv.style.display = 'none';

    try {
        const response = await fetch('/api/image/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                prompt: prompt,
                chat_id: chatId
            })
        });
        const data = await response.json();

        if (data.status === 'success') {
            resultDiv.style.display = 'block';
            document.getElementById('gen-image-title').innerText = data.image_title;
            const img = document.getElementById('gen-image');
            img.src = data.image_url;
            img.style.display = 'block';

            document.getElementById('gen-image-prompt').innerText = data.refined_prompt;

            let statusMsg = "Image generated and saved to Drive.";
            if (data.telegram_status) {
                statusMsg += ` Telegram: ${data.telegram_status}`;
            }
            document.getElementById('gen-image-status').innerText = statusMsg;

            alert('Image Generated Successfully!');
        } else {
            alert('Error: ' + (data.message || data.error));
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// --- IMAGE SEARCH LOGIC ---
document.getElementById('image-search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerText;
    btn.innerText = 'Searching...';
    btn.disabled = true;

    const query = document.getElementById('search-query').value;
    const intent = document.getElementById('search-intent').value;
    const chatId = document.getElementById('search-chat-id').value;

    const resultDiv = document.getElementById('search-result');
    const resultContent = document.getElementById('search-result-content');
    resultDiv.style.display = 'none';

    try {
        const response = await fetch('/api/image/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                intent: intent,
                chat_id: chatId
            })
        });
        const data = await response.json();

        if (data.status === 'error') {
            alert('Error: ' + data.message);
            return;
        }

        if (data.result_status === 'found') {
            resultDiv.style.display = 'block';
            document.getElementById('search-result-title').innerText = data.image_name || 'Image Found';

            let html = `
                <p><strong>Image Name:</strong> ${data.image_name}</p>
                <p><strong>Drive Link:</strong> <a href="${data.image_link}" target="_blank" style="color: #a0c4ff;">View on Google Drive</a></p>
            `;

            if (data.image_id) {
                html += `<p><strong>File ID:</strong> ${data.image_id}</p>`;
            }

            if (intent === 'get') {
                if (data.telegram_status === 'sent') {
                    html += `<p style="color: #4CAF50;"><strong>✓ Telegram:</strong> Image sent successfully!</p>`;
                } else {
                    html += `<p style="color: #ff6b6b;"><strong>Telegram:</strong> ${data.telegram_status}</p>`;
                }
            }

            resultContent.innerHTML = html;
            alert('Image found!');
        } else {
            alert('Image not found in database. Try different keywords.');
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});

// Initial Load
showSection('mail');
