/**
 * Voice Call Eligibility Checker
 * 
 * Checks if a user is eligible for voice calls:
 * - Admin users have unlimited access
 * - Paid users have daily limits (10 minutes)
 * - Free users have no access
 */

/**
 * Check if user is eligible for voice calls
 * @returns {Promise} Resolves with eligibility status
 */
function checkUserEligibility() {
    return new Promise((resolve, reject) => {
        // Check user status from server
        fetch('/api/check_voice_limit')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to check voice call eligibility');
                }
                return response.json();
            })
            .then(data => {
                if (data.is_admin) {
                    // Admin users always have access
                    resolve({
                        eligible: true,
                        isAdmin: true,
                        unlimited: true,
                        message: "Admin user with unlimited access"
                    });
                } else if (data.is_paid) {
                    // Paid users have access with daily limits
                    if (data.can_make_call) {
                        resolve({
                            eligible: true,
                            isAdmin: false,
                            unlimited: false,
                            remaining_minutes: data.remaining_minutes,
                            message: `You have ${data.remaining_minutes} minutes of calling time remaining today`
                        });
                    } else {
                        resolve({
                            eligible: false,
                            isAdmin: false,
                            unlimited: false,
                            remaining_minutes: 0,
                            message: "You've reached your daily limit of voice call minutes"
                        });
                    }
                } else {
                    // Free users don't have access
                    resolve({
                        eligible: false,
                        isAdmin: false,
                        unlimited: false,
                        message: "Voice calls are only available for premium users"
                    });
                }
            })
            .catch(error => {
                console.error('Error checking voice call eligibility:', error);
                // In case of error, default to not eligible
                reject(error);
            });
    });
}

/**
 * Handle eligibility status for voice calls
 * Shows appropriate messages or prompts based on user's status
 */
function handleEligibilityStatus() {
    checkUserEligibility()
        .then(status => {
            // Update UI based on eligibility
            if (status.eligible) {
                // User can make calls
                enableVoiceCallButton();
                
                // If not admin, show remaining time
                if (!status.isAdmin) {
                    showRemainingTimeIndicator(status.remaining_minutes);
                }
            } else {
                // User can't make calls
                if (status.is_paid) {
                    // Paid user who reached limit
                    disableVoiceCallButton("Daily limit reached");
                } else {
                    // Free user
                    disableVoiceCallButton("Premium only");
                    
                    // Add subscription prompt to button
                    document.getElementById('voiceCallBtn').addEventListener('click', showSubscriptionModal);
                }
            }
        })
        .catch(err => {
            console.error('Failed to check eligibility:', err);
            // Disable button on error
            disableVoiceCallButton("Unavailable");
        });
}

/**
 * Enable voice call button
 */
function enableVoiceCallButton() {
    const callButton = document.getElementById('voiceCallBtn');
    if (callButton) {
        callButton.disabled = false;
        callButton.classList.remove('disabled', 'btn-secondary');
        callButton.classList.add('btn-primary');
        
        // Set correct click handler
        callButton.removeEventListener('click', showSubscriptionModal);
        callButton.addEventListener('click', initVoiceCall);
    }
}

/**
 * Disable voice call button with reason
 * @param {string} reason - Reason for disabling
 */
function disableVoiceCallButton(reason) {
    const callButton = document.getElementById('voiceCallBtn');
    if (callButton) {
        callButton.disabled = true;
        callButton.classList.add('disabled', 'btn-secondary');
        callButton.classList.remove('btn-primary');
        callButton.setAttribute('data-bs-toggle', 'tooltip');
        callButton.setAttribute('title', reason);
    }
}

/**
 * Show remaining time indicator for paid users
 * @param {number} minutes - Remaining minutes
 */
function showRemainingTimeIndicator(minutes) {
    const timeIndicator = document.getElementById('remainingTimeIndicator');
    if (timeIndicator) {
        timeIndicator.textContent = `${minutes} min`;
        timeIndicator.style.display = 'inline-block';
    }
}

/**
 * Show subscription modal for free users
 */
function showSubscriptionModal() {
    // If using Bootstrap modal
    const subscriptionModal = new bootstrap.Modal(document.getElementById('subscriptionModal'));
    subscriptionModal.show();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Setup tooltips
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Tooltip !== 'undefined') {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        Array.from(tooltips).forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
    
    // Check eligibility status
    handleEligibilityStatus();
});