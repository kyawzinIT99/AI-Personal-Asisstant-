// Tab Switching
function showSection(sectionId) {
    const sections = [
        'mail', 'calendar', 'leads', 'web', 'chat',
        'weather', 'blog', 'image', 'image-search',
        'clickup', 'faceless', 'contacts'
    ];

    // Hide all sections
    sections.forEach(id => {
        const el = document.getElementById(id + '-section');
        if (el) el.style.display = 'none';
    });

    // Deselect dock items
    document.querySelectorAll('.dock-item').forEach(item => item.classList.remove('active'));

    // Show target section
    const targetSection = document.getElementById(sectionId + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
    }

    // Select dock item
    const dockItems = document.querySelectorAll('.dock-item');
    if (dockItems.length > 0) {
        if (sectionId === 'mail') dockItems[0].classList.add('active');
        if (sectionId === 'calendar') dockItems[1].classList.add('active');
        if (sectionId === 'leads') dockItems[2].classList.add('active');
        if (sectionId === 'contacts') dockItems[3].classList.add('active');
        if (sectionId === 'web') dockItems[4].classList.add('active');
        if (sectionId === 'chat') dockItems[5].classList.add('active');
        if (sectionId === 'weather') dockItems[6].classList.add('active');
        if (sectionId === 'blog') dockItems[7].classList.add('active');
        if (sectionId === 'image') dockItems[8].classList.add('active');
        if (sectionId === 'image-search') dockItems[9].classList.add('active');
        if (sectionId === 'clickup') dockItems[10].classList.add('active');
        if (sectionId === 'faceless') dockItems[11].classList.add('active');
    }

    // Auto load data
    if (sectionId === 'mail') fetchMail();
    if (sectionId === 'calendar') fetchCalendar();
    if (sectionId === 'contacts') fetchContacts();
}

// Global Auth Handling
async function checkAuthResponse(response) {
    if (response.status === 401) {
        document.getElementById('auth-overlay').style.display = 'flex';
        const data = await response.json();
        throw new Error(data.message || 'Authentication required');
    }
    return response;
}

async function handleGoogleAuth() {
    const overlay = document.getElementById('auth-overlay');
    const btn = overlay.querySelector('button');
    const originalText = btn.innerText;

    btn.innerText = 'Authorizing...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/auth/google');
        const data = await response.json();

        if (data.status === 'success') {
            alert('Authentication successful!');
            overlay.style.display = 'none';
            // Refresh current section
            const activeDockItem = document.querySelector('.dock-item.active');
            if (activeDockItem) {
                const title = activeDockItem.getAttribute('title').toLowerCase();
                if (title === 'gmail') fetchMail();
                if (title === 'calendar') fetchCalendar();
                if (title === 'contacts') fetchContacts();
            }
        } else {
            alert('Authentication failed: ' + data.message);
        }
    } catch (error) {
        alert('Network error during authentication: ' + error);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
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
        let response = await fetch('/api/mail/list?max_results=10');
        response = await checkAuthResponse(response);
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
        let response = await fetch('/api/calendar/list?max_results=10');
        response = await checkAuthResponse(response);
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

// --- CONTACTS LOGIC ---

async function fetchContacts() {
    // Clear search bar when refreshing all contacts
    const searchInput = document.getElementById('contacts-search');
    if (searchInput) searchInput.value = '';

    const listContainer = document.getElementById('contacts-list');
    listContainer.innerHTML = '<div class="loading">Loading contacts...</div>';

    try {
        let response = await fetch('/api/contacts/list?max_results=30');
        response = await checkAuthResponse(response);
        const data = await response.json();

        if (data.status === 'success') {
            renderContacts(data.contacts);
        } else {
            listContainer.innerHTML = `<div class="loading">Error: ${data.message}</div>`;
        }
    } catch (error) {
        listContainer.innerHTML = `<div class="loading">Error loading contacts: ${error}</div>`;
    }
}

let contactSearchTimeout = null;
function onContactSearchInput(query) {
    clearTimeout(contactSearchTimeout);
    contactSearchTimeout = setTimeout(() => {
        searchContacts(query);
    }, 500); // 500ms debounce
}

async function searchContacts(query) {
    if (!query || query.trim() === '') {
        fetchContacts();
        return;
    }

    const listContainer = document.getElementById('contacts-list');
    listContainer.innerHTML = '<div class="loading">Searching...</div>';

    try {
        let response = await fetch(`/api/contacts/search?q=${encodeURIComponent(query)}`);
        response = await checkAuthResponse(response);
        const data = await response.json();

        if (data.status === 'success') {
            renderContacts(data.contacts);
        } else {
            listContainer.innerHTML = `<div class="loading">Error: ${data.message}</div>`;
        }
    } catch (error) {
        listContainer.innerHTML = `<div class="loading">Error searching contacts: ${error}</div>`;
    }
}

function renderContacts(contacts) {
    const listContainer = document.getElementById('contacts-list');
    listContainer.innerHTML = '';

    if (!contacts || contacts.length === 0) {
        listContainer.innerHTML = '<div class="placeholder-text" style="grid-column: 1/-1; text-align: center; padding: 40px;">No contacts found.</div>';
        return;
    }

    contacts.forEach(contact => {
        const card = document.createElement('div');
        card.className = 'contact-card';

        // Avatar Logic
        let avatarHtml = '';
        if (contact.photo) {
            avatarHtml = `<div class="contact-avatar" style="background-image: url('${contact.photo}')"></div>`;
        } else {
            const initial = (contact.name && contact.name !== 'Unknown Name' && contact.name !== 'No Name')
                ? contact.name.charAt(0).toUpperCase()
                : '?';
            avatarHtml = `<div class="contact-avatar">${initial}</div>`;
        }

        // Name Fallback
        let displayName = contact.name;
        if (displayName === 'Unknown Name' && contact.email && contact.email !== 'No Email') {
            displayName = contact.email.split('@')[0];
        }

        // Phone/Address
        const phone = (contact.phone && contact.phone !== 'No Phone') ? `📞 ${contact.phone}` : '';
        const address = (contact.address && contact.address !== 'Unknown Address') ? `📍 ${contact.address}` : '';

        card.innerHTML = `
            ${avatarHtml}
            <div class="contact-name">${displayName}</div>
            <div class="contact-email">${contact.email !== 'No Email' ? contact.email : ''}</div>
            <div class="contact-details">
                ${phone ? `<div class="contact-detail-row">${phone}</div>` : ''}
                ${address ? `<div class="contact-detail-row">${address}</div>` : ''}
            </div>
            <div class="contact-actions">
                <button class="btn-primary btn-sm" onclick="alert('Quick action: Call ${displayName}')">Call</button>
                <button class="btn-secondary btn-sm" onclick="alert('Quick action: Email ${displayName}')">Email</button>
            </div>
        `;
        listContainer.appendChild(card);
    });
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
            resultDiv.style.display = 'block';
            resultContent.innerHTML = `<p style="color: #ff6b6b;"><strong>Error:</strong> ${data.message}</p>`;
            resultDiv.scrollIntoView({ behavior: 'smooth' });
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
            resultDiv.scrollIntoView({ behavior: 'smooth' });
        } else {
            resultDiv.style.display = 'block';
            document.getElementById('search-result-title').innerText = 'Not Found';
            resultContent.innerHTML = `<p>Image not found in database. Try different keywords like 'logo' or 'business'.</p>`;
            resultDiv.scrollIntoView({ behavior: 'smooth' });
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

// --- FACELESS VIDEO LOGIC ---

// Generate Video
document.getElementById('faceless-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const subject = document.getElementById('faceless-subject').value;

    // If subject is empty, we tell the backend to use the sheet

    const btn = document.getElementById('btn-generate-video');
    const resultDiv = document.getElementById('faceless-result');
    const statusText = document.getElementById('video-status-text');

    btn.disabled = true;
    btn.innerText = 'Starting Workflow...';
    resultDiv.style.display = 'block';

    try {
        const response = await fetch('/api/video/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subject: subject || null // Send null to imply "read from sheet"
            })
        });
        const data = await response.json();

        if (data.status === 'success') {
            statusText.innerText = 'Workflow started! Job ID: ' + data.project_id;
            pollVideoStatus(data.project_id);
        } else {
            statusText.innerText = 'Error: ' + (data.message || 'Unknown error');
            btn.disabled = false;
            btn.innerText = 'Generate Video';
        }
    } catch (e) {
        statusText.innerText = 'Network Error: ' + e;
        btn.disabled = false;
        btn.innerText = 'Generate Video';
    }
});

async function pollVideoStatus(projectId) {
    const statusText = document.getElementById('video-status-text');
    const previewContainer = document.getElementById('video-preview-container');
    const downloadLink = document.getElementById('video-download-link');

    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/video/status?project_id=${projectId}`);
            const data = await response.json();

            if (data.status === 'success') {
                statusText.innerText = 'Status: ' + data.job_status;

                if (data.job_status === 'done') {
                    clearInterval(interval);
                    statusText.innerText = 'Video Generated Successfully!';
                    previewContainer.style.display = 'block';
                    downloadLink.href = data.video_url;
                    document.getElementById('btn-generate-video').disabled = false;
                    document.getElementById('btn-generate-video').innerText = 'Generate Video';
                } else if (data.job_status === 'error') {
                    clearInterval(interval);
                    statusText.innerText = 'Error generating video.';
                    document.getElementById('btn-generate-video').disabled = false;
                    document.getElementById('btn-generate-video').innerText = 'Generate Video';
                }
            }
        } catch (e) {
            console.error(e);
        }
    }, 5000); // Poll every 5 seconds
}

// --- CLICKUP CRM LOGIC ---

async function fetchClickUpTasks() {
    const listContainer = document.getElementById('clickup-tasks-list');
    listContainer.innerHTML = '<div class="loading">Fetching tasks...</div>';

    // We need a list_id. Usually we'd get them from the user or .env
    // Here we'll try to list tasks for the default list if configured in .env
    // But since we are on the frontend, let's just use a placeholder for now
    // or ask the server for the default list.

    try {
        // Let's assume there's a default list configured or we at least try "0" to see error
        const response = await fetch('/api/clickup/list/0');
        const data = await response.json();

        if (data.status === 'success') {
            listContainer.innerHTML = '';
            if (data.tasks.length === 0) {
                listContainer.innerHTML = '<div class="placeholder-text">No tasks found.</div>';
            } else {
                data.tasks.forEach(task => {
                    const item = document.createElement('div');
                    item.className = 'list-item';
                    item.onclick = () => viewClickUpTask(task.id);
                    item.innerHTML = `
                        <div class="list-item-title">${task.name}</div>
                        <div class="list-item-subtitle">Status: ${task.status.status}</div>
                    `;
                    listContainer.appendChild(item);
                });
            }
        } else {
            listContainer.innerHTML = `<div class="loading">Error: ${data.message}</div>`;
        }
    } catch (error) {
        listContainer.innerHTML = `<div class="loading">Network Error: ${error}</div>`;
    }
}

async function viewClickUpTask(taskId) {
    const detailCard = document.getElementById('clickup-detail-card');
    const content = document.getElementById('clickup-task-content');
    detailCard.style.display = 'block';
    content.innerHTML = '<div class="loading">Loading details...</div>';

    try {
        const response = await fetch(`/api/clickup/task/${taskId}`);
        const data = await response.json();

        if (data.status === 'success') {
            const t = data.task;
            content.innerHTML = `
                <p><strong>Name:</strong> ${t.name}</p>
                <p><strong>Status:</strong> ${t.status.status}</p>
                <p><strong>Description:</strong> ${t.description || 'No description'}</p>
                <p><strong>URL:</strong> <a href="${t.url}" target="_blank" style="color: #a0c4ff;">View in ClickUp</a></p>
                <p><strong>List:</strong> ${t.list.name}</p>
            `;
        } else {
            content.innerHTML = `<div class="loading">Error: ${data.message}</div>`;
        }
    } catch (error) {
        content.innerHTML = `<div class="loading">Network Error: ${error}</div>`;
    }
}

document.getElementById('clickup-task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('clickup-task-id').value.trim();

    // Check if it looks like a Task ID (e.g. 2kzm2vrn-698)
    // ClickUp Task IDs are usually alphanumeric and often contain a hyphen.
    // If it contains spaces or is longer/short of typical ID pattern, we search by name.
    const isIdPattern = /^[a-z0-9-]+$/i.test(input) && input.length >= 7 && input.length <= 15;

    if (isIdPattern) {
        viewClickUpTask(input);
    } else {
        // Assume it's a search name
        searchClickUpTasks(input);
    }
});

async function searchClickUpTasks(query) {
    // Hide detail card and clear previous errors
    document.getElementById('clickup-detail-card').style.display = 'none';

    const listContainer = document.getElementById('clickup-tasks-list');
    listContainer.innerHTML = '<div class="loading">Searching tasks...</div>';

    // Switch to CRM tab view if not already
    showSection('clickup-section');

    try {
        const response = await fetch(`/api/clickup/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.status === 'success') {
            listContainer.innerHTML = '';
            if (data.tasks.length === 0) {
                listContainer.innerHTML = `<div class="placeholder-text">No tasks found for "${query}".</div>`;
            } else {
                data.tasks.forEach(task => {
                    const item = document.createElement('div');
                    item.className = 'list-item';
                    item.onclick = () => viewClickUpTask(task.id);
                    item.innerHTML = `
                        <div class="list-item-title">${task.name}</div>
                        <div class="list-item-subtitle">Status: ${task.status.status}</div>
                    `;
                    listContainer.appendChild(item);
                });
            }
        } else {
            listContainer.innerHTML = `<div class="loading">Error: ${data.message}</div>`;
        }
    } catch (error) {
        listContainer.innerHTML = `<div class="loading">Network error: ${error}</div>`;
    }
}

document.getElementById('clickup-create-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.innerText = 'Creating...';
    btn.disabled = true;

    const payload = {
        name: document.getElementById('clickup-task-name').value,
        description: document.getElementById('clickup-task-desc').value,
        list_id: "0" // Placeholder, should ideally be selectable
    };

    try {
        const response = await fetch('/api/clickup/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            alert('Task created successfully!');
            e.target.reset();
            fetchClickUpTasks();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Network error: ' + error);
    } finally {
        btn.innerText = 'Create Task';
        btn.disabled = false;
    }
});
