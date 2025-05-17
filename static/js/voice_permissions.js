/**
 * Voice Permissions Handler
 * 
 * Handles browser permission requests for microphone and audio output
 * in a user-friendly way without custom notifications.
 */

class VoicePermissionHandler {
    constructor() {
        // Store permission states
        this.micPermission = null;  // null = unknown, true = granted, false = denied
        this.speakerTested = false;
        
        // Permission error container reference
        this.errorContainer = document.getElementById('permission-error');
        
        // Bind methods
        this.requestMicrophonePermission = this.requestMicrophonePermission.bind(this);
        this.testSpeakerOutput = this.testSpeakerOutput.bind(this);
        this.checkPermissionState = this.checkPermissionState.bind(this);
        this.handlePermissionChange = this.handlePermissionChange.bind(this);
        this.showPermissionInstructions = this.showPermissionInstructions.bind(this);
        
        // Set up permission change listener
        if (navigator.permissions && navigator.permissions.query) {
            navigator.permissions.query({ name: 'microphone' })
                .then(permissionStatus => {
                    this.micPermission = permissionStatus.state === 'granted';
                    
                    // Listen for permission changes
                    permissionStatus.onchange = () => {
                        this.handlePermissionChange(permissionStatus);
                    };
                })
                .catch(err => {
                    console.warn('Permission query not supported', err);
                });
        }
    }
    
    /**
     * Request microphone permission using browser's native permission UI
     * @returns {Promise} Resolves with media stream if permission granted
     */
    requestMicrophonePermission() {
        return new Promise((resolve, reject) => {
            // Show a subtle pre-notification to prepare the user for the browser's dialog
            this.showPrePermissionNotice('microphone');
            
            // Short delay to let the user read the notice before browser dialog appears
            setTimeout(() => {
                // This triggers the browser's native permission dialog - not a custom notification
                navigator.mediaDevices.getUserMedia({ audio: true, video: false })
                    .then(stream => {
                        this.micPermission = true;
                        
                        // Hide the pre-permission notice
                        this.hidePrePermissionNotice();
                        
                        // If we have an error displayed, clear it
                        if (this.errorContainer) {
                            this.errorContainer.style.display = 'none';
                        }
                        
                        // Show brief success message
                        this.showPermissionSuccessMessage('microphone');
                        
                        resolve(stream);
                    })
                    .catch(err => {
                        this.micPermission = false;
                        
                        // Hide the pre-permission notice
                        this.hidePrePermissionNotice();
                        
                        // Check specific error
                        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                            this.showPermissionInstructions('microphone');
                        } else {
                            console.error('Microphone error:', err);
                            this.showGenericErrorMessage(err.message || 'Could not access microphone');
                        }
                        
                        reject(err);
                    });
            }, 1000); // 1 second delay before showing browser dialog
        });
    }
    
    /**
     * Show a subtle guidance message before browser permission dialog appears
     * This helps users understand what to expect and why permissions are needed
     * @param {string} type - Type of permission (microphone or speaker)
     */
    showPrePermissionNotice(type) {
        // First, check if we can show pre-permission notice
        if (!this.errorContainer) {
            // Create one if it doesn't exist
            this.errorContainer = document.createElement('div');
            this.errorContainer.id = 'permission-error';
            this.errorContainer.style.display = 'none';
            this.errorContainer.style.position = 'absolute';
            this.errorContainer.style.top = '70px';
            this.errorContainer.style.right = '10px';
            this.errorContainer.style.width = '300px';
            this.errorContainer.style.zIndex = '1000';
            document.body.appendChild(this.errorContainer);
        }
        
        // Customize message based on permission type
        let title = type === 'microphone' ? 'Voice Call Permission' : 'Audio Permission';
        let message = type === 'microphone' 
            ? 'Your browser will ask permission to use your microphone for voice calling with Sophia.'
            : 'Your browser will ask permission to play audio for Sophia\'s voice.';
            
        this.errorContainer.innerHTML = `
            <div class="alert alert-info">
                <div class="d-flex align-items-center mb-2">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>${title}</strong>
                </div>
                <p class="mb-0">${message}</p>
                <p class="mb-0 mt-1"><small>Please click "Allow" in the browser dialog.</small></p>
            </div>
        `;
        this.errorContainer.style.display = 'block';
        
        // Add subtle fade animation
        this.errorContainer.style.opacity = '0';
        this.errorContainer.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
            this.errorContainer.style.opacity = '1';
        }, 10);
    }
    
    /**
     * Hide the pre-permission notice
     */
    hidePrePermissionNotice() {
        if (this.errorContainer) {
            // Fade out
            this.errorContainer.style.opacity = '0';
            setTimeout(() => {
                this.errorContainer.style.display = 'none';
            }, 300);
        }
    }
    
    /**
     * Show a brief success message when permission is granted
     * @param {string} type - Type of permission (microphone or speaker)
     */
    showPermissionSuccessMessage(type) {
        if (!this.errorContainer) return;
        
        this.errorContainer.innerHTML = `
            <div class="alert alert-success">
                <div class="d-flex align-items-center">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>${type.charAt(0).toUpperCase() + type.slice(1)} access granted</strong>
                </div>
            </div>
        `;
        this.errorContainer.style.display = 'block';
        this.errorContainer.style.opacity = '1';
        
        // Auto-hide after 2 seconds
        setTimeout(() => {
            this.errorContainer.style.opacity = '0';
            setTimeout(() => {
                this.errorContainer.style.display = 'none';
            }, 300);
        }, 2000);
    }
    
    /**
     * Show a generic error message
     * @param {string} message - Error message
     */
    showGenericErrorMessage(message) {
        if (!this.errorContainer) return;
        
        this.errorContainer.innerHTML = `
            <div class="alert alert-danger">
                <div class="d-flex align-items-center mb-2">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    <strong>Error</strong>
                </div>
                <p class="mb-1">${message}</p>
                <button class="btn btn-sm btn-danger mt-2" onclick="voicePermissions.requestPermissions()">
                    Try Again
                </button>
            </div>
        `;
        this.errorContainer.style.display = 'block';
        this.errorContainer.style.opacity = '1';
    }
    
    /**
     * Test speaker/audio output permission
     * @returns {Promise} Resolves if audio output works
     */
    testSpeakerOutput() {
        return new Promise((resolve, reject) => {
            try {
                // Create audio context for testing audio output
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                
                // Create a short beep sound to test speaker permission
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                // Very quiet, short sound
                gainNode.gain.value = 0.01;
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                // Start and stop after 10ms
                oscillator.start();
                oscillator.stop(audioContext.currentTime + 0.01);
                
                // Mark speakers as tested
                this.speakerTested = true;
                
                // Resolve after allowing time for the sound to play
                setTimeout(() => {
                    resolve(true);
                }, 100);
            } catch (err) {
                console.error('Speaker test failed:', err);
                this.showPermissionInstructions('speaker');
                reject(err);
            }
        });
    }
    
    /**
     * Check current permission state
     * @returns {Promise} Resolves with permission state object
     */
    async checkPermissionState() {
        // Default state if Permissions API not available
        let state = {
            microphone: this.micPermission,
            speaker: this.speakerTested
        };
        
        // Try to get more accurate state with Permissions API if available
        if (navigator.permissions && navigator.permissions.query) {
            try {
                const micPermission = await navigator.permissions.query({ name: 'microphone' });
                state.microphone = micPermission.state === 'granted';
            } catch (err) {
                console.warn('Microphone permission query not supported');
            }
        }
        
        return state;
    }
    
    /**
     * Handle permission state changes
     * @param {PermissionStatus} permissionStatus - Permission status object
     */
    handlePermissionChange(permissionStatus) {
        if (permissionStatus.state === 'granted') {
            this.micPermission = true;
            
            // Clear any error messages
            if (this.errorContainer) {
                this.errorContainer.style.display = 'none';
            }
            
            // Dispatch event for permission granted
            window.dispatchEvent(new CustomEvent('voice-permission-granted', {
                detail: { type: 'microphone' }
            }));
        } else {
            this.micPermission = false;
            
            // Show instructions if denied
            if (permissionStatus.state === 'denied') {
                this.showPermissionInstructions('microphone');
            }
            
            // Dispatch event for permission denied
            window.dispatchEvent(new CustomEvent('voice-permission-denied', {
                detail: { type: 'microphone' }
            }));
        }
    }
    
    /**
     * Show user-friendly instructions for enabling permissions
     * @param {string} type - Type of permission (microphone or speaker)
     */
    showPermissionInstructions(type) {
        if (!this.errorContainer) {
            // Create error container if it doesn't exist
            this.errorContainer = document.createElement('div');
            this.errorContainer.id = 'permission-error';
            this.errorContainer.style.display = 'none';
            this.errorContainer.style.position = 'absolute';
            this.errorContainer.style.top = '70px';
            this.errorContainer.style.right = '10px';
            this.errorContainer.style.width = '300px';
            this.errorContainer.style.zIndex = '1000';
            document.body.appendChild(this.errorContainer);
        }
        
        const browserName = this.detectBrowser();
        
        // Build browser-specific visual instructions with illustrations
        let visualGuide = '';
        let instructionText = '';
        
        // Title based on permission type
        const title = type === 'microphone' ? 'Microphone Access Required' : 'Audio Access Required';
        
        // Define browser-specific instructions with illustrations/icons
        switch (browserName) {
            case 'chrome':
                visualGuide = `
                    <div class="text-center mb-2">
                        <div style="background-color: #f0f0f0; border-radius: 6px; padding: 8px; display: inline-block;">
                            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                                <i class="fas fa-lock" style="color: #5f6368;"></i>
                                <span style="color: #5f6368; font-family: Arial;">https://example.com</span>
                                <i class="fas fa-chevron-down" style="color: #5f6368; font-size: 0.8em;"></i>
                            </div>
                        </div>
                    </div>
                `;
                instructionText = `
                    <p>Click the lock icon <i class="fas fa-lock"></i> in your address bar, then select "<strong>Site settings</strong>".
                    Find "${type}" in the permissions list and set it to "Allow".</p>
                `;
                break;
                
            case 'firefox':
                visualGuide = `
                    <div class="text-center mb-2">
                        <div style="background-color: #f0f0f0; border-radius: 6px; padding: 8px; display: inline-block;">
                            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                                <i class="fas fa-shield-alt" style="color: #45a1ff;"></i>
                                <span style="color: #5f6368; font-family: Arial;">https://example.com</span>
                            </div>
                        </div>
                    </div>
                `;
                instructionText = `
                    <p>Click the shield icon <i class="fas fa-shield-alt"></i> in your address bar, then select "<strong>Connection Secure</strong>".
                    Find "${type}" in the permissions section and allow access.</p>
                `;
                break;
                
            case 'safari':
                visualGuide = `
                    <div class="text-center mb-2">
                        <div style="background-color: #f0f0f0; border-radius: 6px; padding: 8px; display: inline-block;">
                            <div style="display: flex; align-items: center; justify-content: center; gap: 5px;">
                                <i class="fas fa-lock" style="color: #5f6368;"></i>
                                <span style="color: #5f6368; font-family: Arial;">example.com</span>
                            </div>
                        </div>
                    </div>
                `;
                instructionText = `
                    <p>Click Safari in the menu bar, then "<strong>Preferences > Websites > ${type.charAt(0).toUpperCase() + type.slice(1)}</strong>" 
                    and set this website to "Allow".</p>
                `;
                break;
                
            default:
                visualGuide = `
                    <div class="text-center mb-2">
                        <i class="fas fa-globe" style="font-size: 2em; color: #6c757d;"></i>
                    </div>
                `;
                instructionText = `
                    <p>Check your browser settings to allow ${type} access for this website.</p>
                `;
        }
        
        // Create rich notification with visual guide
        this.errorContainer.innerHTML = `
            <div class="alert alert-warning shadow">
                <div class="d-flex align-items-center mb-2">
                    <i class="fas fa-exclamation-circle me-2 text-warning" style="font-size: 1.2em;"></i>
                    <strong>${title}</strong>
                    <button type="button" class="btn-close ms-auto" style="font-size: 0.7em;" 
                            onclick="document.getElementById('permission-error').style.display='none'"></button>
                </div>
                
                <p class="mb-2">To use voice calling with Sophia, your browser needs permission to access your ${type}.</p>
                
                ${visualGuide}
                
                ${instructionText}
                
                <div class="d-flex justify-content-center mt-3">
                    <button class="btn btn-sm btn-warning" onclick="voicePermissions.requestPermissions()">
                        <i class="fas fa-redo-alt me-1"></i> Try Again
                    </button>
                </div>
            </div>
        `;
        
        // Animate the notification entry
        this.errorContainer.style.display = 'block';
        this.errorContainer.style.opacity = '0';
        this.errorContainer.style.transform = 'translateY(-10px)';
        this.errorContainer.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            this.errorContainer.style.opacity = '1';
            this.errorContainer.style.transform = 'translateY(0)';
        }, 10);
    }
    
    /**
     * Request all required permissions for voice calls
     * @returns {Promise} Resolves when all permissions are granted
     */
    async requestPermissions() {
        try {
            // First get microphone permission
            const micStream = await this.requestMicrophonePermission();
            
            // Then test speaker output
            await this.testSpeakerOutput();
            
            // Return the microphone stream for use
            return {
                success: true,
                stream: micStream
            };
        } catch (err) {
            console.error('Permission request failed:', err);
            return {
                success: false,
                error: err
            };
        }
    }
    
    /**
     * Detect browser for showing accurate instructions
     * @returns {string} Browser name (chrome, firefox, safari, etc.)
     */
    detectBrowser() {
        const userAgent = navigator.userAgent.toLowerCase();
        
        if (userAgent.indexOf('chrome') > -1) return 'chrome';
        if (userAgent.indexOf('firefox') > -1) return 'firefox';
        if (userAgent.indexOf('safari') > -1) return 'safari';
        if (userAgent.indexOf('edge') > -1) return 'edge';
        if (userAgent.indexOf('opera') > -1) return 'opera';
        
        return 'unknown';
    }
}

// Create global instance
const voicePermissions = new VoicePermissionHandler();

// Function to initialize voice call with permissions
function initVoiceCall() {
    // Check if user is eligible for voice calls first
    // We'll use the checkUserEligibility function declared elsewhere
    if (typeof checkUserEligibility === 'function') {
        checkUserEligibility()
            .then(eligible => {
                if (eligible) {
                    // User is eligible, request permissions
                    return voicePermissions.requestPermissions();
                } else {
                    // User not eligible - this would handle showing subscription modal
                    throw new Error('User not eligible for voice calls');
                }
            })
            .then(result => {
                if (result.success) {
                    // Permissions granted, start voice call
                    startVoiceCall(result.stream);
                }
            })
            .catch(err => {
                console.error('Failed to start voice call:', err);
            });
    } else {
        // Fallback if eligibility check not defined
        voicePermissions.requestPermissions()
            .then(result => {
                if (result.success) {
                    startVoiceCall(result.stream);
                }
            });
    }
}

// This function will be implemented elsewhere
function startVoiceCall(microphoneStream) {
    // Placeholder for actual implementation
    console.log('Starting voice call with stream:', microphoneStream);
}