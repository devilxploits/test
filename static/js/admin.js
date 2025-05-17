document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const settingsForm = document.getElementById('settings-form');
    const contentGeneratorForm = document.getElementById('content-generator-form');
    const contentTable = document.getElementById('content-table');
    const conversationsTable = document.getElementById('conversations-table');
    const postScheduleForm = document.getElementById('postScheduleForm');
    const saveScheduleBtn = document.getElementById('saveScheduleBtn');
    
    // Initialize date pickers
    const datepickers = document.querySelectorAll('.datepicker');
    if (datepickers.length) {
        datepickers.forEach(dp => {
            // This would use a date picker library in a real implementation
            // For now, we'll use the HTML5 datetime-local input
        });
    }
    
    // Load settings from server
    function loadSettings() {
        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                // Populate form fields with settings data
                document.getElementById('personalityTraits').value = data.personality || '';
                document.getElementById('contentStyle').value = data.content_style || '';
                document.getElementById('responseLength').value = data.response_length || 100;
                document.getElementById('flirtLevel').value = data.flirt_level || 5;
                document.getElementById('postFrequency').value = data.post_frequency || 1;
                
                // Update range input displays
                updateRangeDisplay('responseLength', 'responseLengthDisplay');
                updateRangeDisplay('flirtLevel', 'flirtLevelDisplay');
                updateRangeDisplay('postFrequency', 'postFrequencyDisplay');
                
                // Instagram settings
                const instagramSettings = data.instagram_settings || {};
                document.getElementById('hashtags').value = instagramSettings.hashtag_count || 5;
                
                // Telegram settings
                const telegramSettings = data.telegram_settings || {};
                document.getElementById('autoReply').checked = telegramSettings.auto_reply !== false;
                
                // API Settings
                // Kobold Horde settings
                document.getElementById('koboldApiKey').value = ''; // Don't display API key for security
                document.getElementById('koboldModel').value = data.kobold_model || 'Mixtral-8x7B-Instruct-v0.1';
                document.getElementById('allowNsfw').checked = data.allow_nsfw || false;
                
                // Piper TTS settings
                document.getElementById('piperApiKey').value = ''; // Don't display API key for security
                document.getElementById('useTts').checked = data.use_tts || false;
                document.getElementById('ttsVoiceId').value = data.tts_voice_id || 'female_casual';
                document.getElementById('ttsSpeed').value = data.tts_speed || 1.0;
                updateRangeDisplay('ttsSpeed', 'ttsSpeedDisplay');
            })
            .catch(error => {
                console.error('Error loading settings:', error);
                showAlert('danger', 'Failed to load settings. Please try again.');
            });
    }
    
    // Update display for range inputs
    function updateRangeDisplay(inputId, displayId) {
        const input = document.getElementById(inputId);
        const display = document.getElementById(displayId);
        if (input && display) {
            display.textContent = input.value;
            
            // Add event listener to update display when range changes
            input.addEventListener('input', function() {
                display.textContent = this.value;
            });
        }
    }
    
    // Load content posts with pagination
    function loadContentPosts(page = 1) {
        fetch(`/api/content?page=${page}&per_page=10`)
            .then(response => response.json())
            .then(data => {
                // Clear existing rows
                const tbody = contentTable.querySelector('tbody');
                tbody.innerHTML = '';
                
                // Add posts to table
                data.posts.forEach(post => {
                    const row = document.createElement('tr');
                    
                    // Format status with appropriate badge
                    let statusBadge = '';
                    switch (post.status) {
                        case 'draft':
                            statusBadge = '<span class="badge bg-secondary">Draft</span>';
                            break;
                        case 'scheduled':
                            statusBadge = '<span class="badge bg-warning text-dark">Scheduled</span>';
                            break;
                        case 'published':
                            statusBadge = '<span class="badge bg-success">Published</span>';
                            break;
                        case 'failed':
                            statusBadge = '<span class="badge bg-danger">Failed</span>';
                            break;
                    }
                    
                    // Format scheduled and published dates
                    const scheduledDate = post.scheduled_for ? new Date(post.scheduled_for).toLocaleString() : 'Not scheduled';
                    const publishedDate = post.published_at ? new Date(post.published_at).toLocaleString() : 'Not published';
                    
                    row.innerHTML = `
                        <td>${post.id}</td>
                        <td>${post.title}</td>
                        <td>${post.caption}</td>
                        <td>${statusBadge}</td>
                        <td>${scheduledDate}</td>
                        <td>${publishedDate}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary edit-content" data-id="${post.id}">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-content" data-id="${post.id}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    `;
                    
                    tbody.appendChild(row);
                });
                
                // Update pagination if needed
                // This would be implemented with pagination controls in a real app
            })
            .catch(error => {
                console.error('Error loading content posts:', error);
                showAlert('danger', 'Failed to load content posts. Please try again.');
            });
    }
    
    // Show alert message
    function showAlert(type, message) {
        const alertContainer = document.getElementById('alert-container');
        
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            alertContainer.appendChild(alert);
            
            // Auto dismiss after 5 seconds
            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => {
                    alertContainer.removeChild(alert);
                }, 300);
            }, 5000);
        }
    }
    
    // Handle settings form submission
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Collect form data
            const formData = {
                personality: document.getElementById('personalityTraits').value,
                content_style: document.getElementById('contentStyle').value,
                response_length: parseInt(document.getElementById('responseLength').value),
                flirt_level: parseInt(document.getElementById('flirtLevel').value),
                post_frequency: parseInt(document.getElementById('postFrequency').value),
                
                // Instagram settings
                instagram_settings: {
                    hashtag_count: parseInt(document.getElementById('hashtags').value),
                    emoji_level: document.getElementById('emojiLevel').value
                },
                
                // Telegram settings
                telegram_settings: {
                    use_stickers: document.getElementById('useStickers').checked,
                    auto_reply: document.getElementById('autoReply').checked
                },
                
                // Kobold Horde API settings
                kobold_model: document.getElementById('koboldModel').value,
                allow_nsfw: document.getElementById('allowNsfw').checked,
                
                // Piper TTS settings
                use_tts: document.getElementById('useTts').checked,
                tts_voice_id: document.getElementById('ttsVoiceId').value,
                tts_speed: parseFloat(document.getElementById('ttsSpeed').value)
            };
            
            // Add API keys if they are provided (not empty)
            const koboldApiKey = document.getElementById('koboldApiKey').value;
            if (koboldApiKey) {
                formData.kobold_api_key = koboldApiKey;
            }
            
            const piperApiKey = document.getElementById('piperApiKey').value;
            if (piperApiKey) {
                formData.piper_api_key = piperApiKey;
            }
            
            // Save settings to server
            fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', 'Settings saved successfully!');
                } else {
                    showAlert('danger', 'Failed to save settings: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                showAlert('danger', 'Failed to save settings. Please try again.');
            });
        });
    }
    
    // Handle content generator form submission
    if (contentGeneratorForm) {
        contentGeneratorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const theme = document.getElementById('content-theme').value;
            const style = document.getElementById('content-style-select').value;
            
            // Get platform checkboxes
            const platforms = [];
            document.querySelectorAll('input[name="platforms"]:checked').forEach(cb => {
                platforms.push(cb.value);
            });
            
            // Check if at least one platform is selected
            if (platforms.length === 0) {
                showAlert('warning', 'Please select at least one platform.');
                return;
            }
            
            // Get scheduling information
            const scheduleContent = document.getElementById('schedule-content').checked;
            const scheduleDateTime = document.getElementById('schedule-datetime').value;
            
            // Prepare request data
            const requestData = {
                generate: true,
                theme: theme,
                style: style,
                platforms: platforms
            };
            
            // Add scheduling if enabled
            if (scheduleContent && scheduleDateTime) {
                requestData.schedule_for = scheduleDateTime;
            }
            
            // Show loading state
            const submitButton = contentGeneratorForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
            submitButton.disabled = true;
            
            // Send request to server
            fetch('/api/content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                // Reset button state
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                
                if (data.success) {
                    showAlert('success', 'Content generated successfully! ' + (scheduleContent ? 'It has been scheduled.' : ''));
                    
                    // Reset form
                    contentGeneratorForm.reset();
                    
                    // Reload content table
                    loadContentPosts();
                } else {
                    showAlert('danger', 'Failed to generate content: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                // Reset button state
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                
                console.error('Error generating content:', error);
                showAlert('danger', 'Failed to generate content. Please try again.');
            });
        });
    }
    
    // Handle content deletion
    if (contentTable) {
        contentTable.addEventListener('click', function(e) {
            // Check if delete button was clicked
            if (e.target.closest('.delete-content')) {
                const button = e.target.closest('.delete-content');
                const postId = button.dataset.id;
                
                if (confirm('Are you sure you want to delete this content?')) {
                    // Send delete request to server
                    fetch(`/api/content?id=${postId}`, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showAlert('success', 'Content deleted successfully.');
                            
                            // Reload content table
                            loadContentPosts();
                        } else {
                            showAlert('danger', 'Failed to delete content: ' + (data.error || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        console.error('Error deleting content:', error);
                        showAlert('danger', 'Failed to delete content. Please try again.');
                    });
                }
            }
            
            // Handle edit button (would open a modal in a real implementation)
            if (e.target.closest('.edit-content')) {
                const button = e.target.closest('.edit-content');
                const postId = button.dataset.id;
                
                // In a real app, this would open a modal with the content details
                showAlert('info', 'Edit functionality would open a modal for post ID: ' + postId);
            }
        });
    }
    
    // Load schedule settings
    function loadScheduleSettings() {
        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                // Populate schedule form fields with data
                document.getElementById('totalPostsPerDay').value = data.post_frequency || 2;
                document.getElementById('imagesPerDay').value = data.images_per_day || 1;
                document.getElementById('reelsPerDay').value = data.reels_per_day || 1;
                document.getElementById('postTimeStart').value = data.post_time_start || 9;
                document.getElementById('postTimeEnd').value = data.post_time_end || 21;
                
                // Set post days checkboxes
                const postDays = data.post_days || [0, 1, 2, 3, 4, 5, 6]; // Default all days selected
                const dayCheckboxes = document.querySelectorAll('.post-day-checkbox');
                dayCheckboxes.forEach(checkbox => {
                    checkbox.checked = postDays.includes(parseInt(checkbox.value));
                });
                
                // Set auto-schedule switch
                document.getElementById('autoScheduleSwitch').checked = data.auto_schedule !== false;
            })
            .catch(error => {
                console.error('Error loading schedule settings:', error);
                showAlert('danger', 'Failed to load schedule settings. Please try again.');
            });
    }
    
    // Save schedule settings
    function saveScheduleSettings() {
        // Collect days that are checked
        const selectedDays = [];
        document.querySelectorAll('.post-day-checkbox:checked').forEach(checkbox => {
            selectedDays.push(parseInt(checkbox.value));
        });
        
        // Prepare data to save
        const scheduleData = {
            post_frequency: parseInt(document.getElementById('totalPostsPerDay').value),
            images_per_day: parseInt(document.getElementById('imagesPerDay').value),
            reels_per_day: parseInt(document.getElementById('reelsPerDay').value),
            post_time_start: parseInt(document.getElementById('postTimeStart').value),
            post_time_end: parseInt(document.getElementById('postTimeEnd').value),
            post_days: selectedDays,
            auto_schedule: document.getElementById('autoScheduleSwitch').checked
        };
        
        // Save settings to server
        fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scheduleData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', 'Schedule settings saved successfully!');
                
                // Refresh post queue
                loadPostQueue();
            } else {
                showAlert('danger', 'Failed to save schedule settings: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error saving schedule settings:', error);
            showAlert('danger', 'Failed to save schedule settings. Please try again.');
        });
    }
    
    // Load posts in queue
    function loadPostQueue() {
        fetch('/api/content?status=scheduled&per_page=10')
            .then(response => response.json())
            .then(data => {
                // Get the post queue table body
                const tableBody = document.querySelector('#postQueueTable tbody');
                if (!tableBody) return;
                
                // Clear existing rows
                tableBody.innerHTML = '';
                
                // Add scheduled posts to table
                if (data.posts && data.posts.length > 0) {
                    data.posts.forEach(post => {
                        const row = document.createElement('tr');
                        
                        // Format scheduled date
                        const scheduledDate = post.scheduled_for ? new Date(post.scheduled_for).toLocaleString() : 'Not scheduled';
                        
                        // Determine content type icon
                        let contentTypeIcon = '<i class="fas fa-image fa-lg text-muted"></i>';
                        if (post.content_type === 'video' || post.content_type === 'reel') {
                            contentTypeIcon = '<i class="fas fa-video fa-lg text-muted"></i>';
                        }
                        
                        row.innerHTML = `
                            <td>
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" checked>
                                </div>
                            </td>
                            <td>
                                <div class="d-flex align-items-center">
                                    <div class="me-3 bg-dark rounded" style="width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border-color);">
                                        ${contentTypeIcon}
                                    </div>
                                    <div>
                                        <h6 class="mb-1">${post.title || 'Untitled'}</h6>
                                        <p class="small text-muted mb-0">${post.caption || 'No caption'}</p>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <div class="d-flex flex-column">
                                    ${post.platforms && post.platforms.includes('instagram') ? '<span class="badge bg-info mb-1">Instagram</span>' : ''}
                                    ${post.platforms && post.platforms.includes('telegram') ? '<span class="badge bg-primary mb-1">Telegram</span>' : ''}
                                </div>
                            </td>
                            <td>${scheduledDate}</td>
                            <td><span class="badge bg-warning text-dark">Scheduled</span></td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary edit-post" data-id="${post.id}">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger delete-post" data-id="${post.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        `;
                        
                        tableBody.appendChild(row);
                    });
                } else {
                    // Show empty state
                    const emptyRow = document.createElement('tr');
                    emptyRow.innerHTML = `
                        <td colspan="6" class="text-center py-4">
                            <div class="d-flex flex-column align-items-center">
                                <i class="fas fa-calendar-alt fa-3x text-muted mb-3"></i>
                                <h6 class="mb-1">No scheduled posts</h6>
                                <p class="small text-muted">Posts will appear here once scheduled</p>
                            </div>
                        </td>
                    `;
                    tableBody.appendChild(emptyRow);
                }
            })
            .catch(error => {
                console.error('Error loading post queue:', error);
                showAlert('danger', 'Failed to load post queue. Please try again.');
            });
    }
    
    // Add event listener to save schedule button
    if (saveScheduleBtn) {
        saveScheduleBtn.addEventListener('click', saveScheduleSettings);
    }
    
    // Initialize page
    if (settingsForm) {
        loadSettings();
    }
    
    // Initialize schedule settings and post queue
    if (postScheduleForm) {
        loadScheduleSettings();
        loadPostQueue();
    }
    
    if (contentTable) {
        loadContentPosts();
    }
    
    // Set up refresh button for content
    const refreshContentBtn = document.getElementById('refresh-content');
    if (refreshContentBtn) {
        refreshContentBtn.addEventListener('click', function() {
            loadContentPosts();
        });
    }
    
    // Toggle schedule datetime input based on checkbox
    const scheduleCheckbox = document.getElementById('schedule-content');
    const scheduleDatetimeInput = document.getElementById('schedule-datetime');
    
    if (scheduleCheckbox && scheduleDatetimeInput) {
        scheduleCheckbox.addEventListener('change', function() {
            scheduleDatetimeInput.disabled = !this.checked;
            if (this.checked) {
                // Set default to tomorrow at noon
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                tomorrow.setHours(12, 0, 0, 0);
                
                // Format for datetime-local input
                const formattedDate = tomorrow.toISOString().slice(0, 16);
                scheduleDatetimeInput.value = formattedDate;
            }
        });
        
        // Initial state
        scheduleDatetimeInput.disabled = !scheduleCheckbox.checked;
    }
});
