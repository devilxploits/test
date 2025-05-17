/**
 * Voice interaction functionality for Sophia AI
 * Handles speech recognition and text-to-speech using browser APIs
 * and the server-side Piper TTS service for high-quality natural voice synthesis
 * 
 * Piper TTS is a neural text-to-speech system that provides more natural and
 * expressive voices compared to browser-based TTS.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get UI elements
    const voiceCallButton = document.getElementById('voice-call-button');
    const endCallButton = document.getElementById('end-call-button');
    const userSpeechText = document.getElementById('user-speech-text');
    const sophiaResponseText = document.getElementById('sophia-response-text');
    const callStatus = document.getElementById('call-status');
    const voiceCallModal = new bootstrap.Modal(document.getElementById('voice-call-modal'));
    
    // State variables
    let callInProgress = false;
    let permissionDenied = false;
    
    // Speech recognition setup
    let recognition = null;
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
    } else if ('SpeechRecognition' in window) {
        recognition = new SpeechRecognition();
    }
    
    // Set recognition properties if available
    if (recognition) {
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US'; // Default language
        
        // Handle recognition results
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            userSpeechText.textContent = transcript;
            getSophiaResponse(transcript);
        };
        
        // Handle errors
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            
            if (event.error === 'not-allowed') {
                permissionDenied = true;
                updateCallStatus('Microphone permission denied. Please allow microphone access.');
                // Show a more prominent alert, but without URL information
                alert('Microphone permission denied. Please allow microphone access to use voice calls.');
                setTimeout(() => {
                    endVoiceCall();
                }, 2000);
            } else {
                updateCallStatus('Error: ' + event.error);
                setTimeout(startListening, 2000); // Try again after delay
            }
        };
        
        // When recognition ends, restart it for continuous conversation
        recognition.onend = function() {
            // Don't restart if call was manually ended or permission denied
            if (callInProgress && !permissionDenied) {
                setTimeout(startListening, 1000); // Brief pause between listening sessions
            }
        };
    }
    
    // Attach event listeners
    if (voiceCallButton) {
        voiceCallButton.addEventListener('click', function() {
            if (callInProgress) {
                endVoiceCall(); // End call if already in progress
            } else {
                requestMicrophonePermission();
            }
        });
    }
    
    if (endCallButton) {
        endCallButton.addEventListener('click', endVoiceCall);
    }
    
    // Close modal should also end call
    document.getElementById('voice-call-modal').addEventListener('hidden.bs.modal', function () {
        endVoiceCall();
    });
    
    /**
     * Request microphone permission before starting the call
     */
    function requestMicrophonePermission() {
        // Reset permission denied flag
        permissionDenied = false;
        
        // Force a brand new permission request by adding a unique constraint to defeat caching
        // This ensures the browser prompts for permission every time
        navigator.mediaDevices.getUserMedia({ 
            audio: { 
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                // Add a random timestamp to force a new permission request each time
                deviceId: 'force-permission-' + Date.now()
            } 
        })
        .then(function(stream) {
            // Permission granted
            stream.getTracks().forEach(track => track.stop()); // Stop the tracks immediately
            startVoiceCall();
        })
        .catch(function(err) {
            console.error('Microphone permission denied');
            permissionDenied = true;
            alert('Microphone permission is required for voice calls. Please allow microphone access and try again.');
        });
    }
    
    /**
     * Start a voice call with Sophia
     */
    function startVoiceCall() {
        if (callInProgress) return; // Prevent multiple call sessions
        
        callInProgress = true;
        voiceCallButton.innerHTML = '<i class="fas fa-phone-slash"></i> End Call';
        voiceCallButton.classList.add('btn-danger');
        voiceCallButton.classList.remove('btn-outline-light');
        
        voiceCallModal.show();
        updateCallStatus('Connecting...');
        
        // Delay starting recognition to allow modal to appear
        setTimeout(() => {
            updateCallStatus('Listening...');
            startListening();
        }, 1000);
    }
    
    /**
     * End the current voice call
     */
    function endVoiceCall() {
        if (recognition) {
            try {
                recognition.stop();
            } catch (e) {
                // Ignore errors when stopping recognition
            }
        }
        
        // Stop any playing audio
        const audios = document.getElementsByTagName('audio');
        for (let i = 0; i < audios.length; i++) {
            audios[i].pause();
            audios[i].currentTime = 0;
        }
        
        // Cancel speech synthesis if in progress
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        
        // Reset UI
        updateCallStatus('Call ended');
        callInProgress = false;
        voiceCallButton.innerHTML = '<i class="fas fa-phone"></i> Call';
        voiceCallButton.classList.remove('btn-danger');
        voiceCallButton.classList.add('btn-outline-light');
        
        // Hide modal after a slight delay
        setTimeout(() => {
            voiceCallModal.hide();
        }, 500);
    }
    
    /**
     * Start listening for user speech
     */
    function startListening() {
        if (!recognition) {
            updateCallStatus('Speech recognition not supported in this browser');
            return;
        }
        
        if (permissionDenied) {
            updateCallStatus('Microphone permission denied. Please allow microphone access.');
            setTimeout(endVoiceCall, 2000);
            return;
        }
        
        try {
            recognition.start();
            updateCallStatus('Listening...');
            userSpeechText.textContent = 'Listening...';
        } catch (error) {
            console.error('Error starting recognition:', error);
            updateCallStatus('Error starting voice recognition');
        }
    }
    
    /**
     * Get response from Sophia AI based on user's speech
     * Using Piper TTS for high-quality voice synthesis
     */
    function getSophiaResponse(userText) {
        updateCallStatus('Thinking...');
        
        // Make API call to get Sophia's response
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userText,
                use_tts: true,
                tts_provider: 'piper' // Specify to use Piper TTS
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Display the text response
                sophiaResponseText.textContent = data.response;
                
                // If TTS is enabled and audio URL is provided from Piper TTS
                if (data.audio_url) {
                    updateCallStatus('Speaking with Piper voice...');
                    speakWithAudio(data.audio_url);
                } else {
                    // Try to get Piper TTS audio directly
                    generatePiperTTS(data.response);
                }
                
                // Also add to chat history in the main chat window
                if (typeof addSophiaMessage === 'function') {
                    addSophiaMessage(data.response);
                }
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('Error getting Sophia response:', error);
            sophiaResponseText.textContent = "I'm sorry, I couldn't process your request right now.";
            updateCallStatus('Error occurred');
            
            // Only restart listening if call is still in progress
            if (callInProgress && !permissionDenied) {
                setTimeout(startListening, 3000);
            }
        });
    }
    
    /**
     * Speak text using browser's speech synthesis
     */
    function speakText(text) {
        if ('speechSynthesis' in window) {
            const speech = new SpeechSynthesisUtterance(text);
            speech.lang = 'en-US';
            speech.rate = 1.0;
            speech.pitch = 1.0;
            
            // Use a female voice if available
            const voices = window.speechSynthesis.getVoices();
            const femaleVoice = voices.find(voice => 
                voice.name.includes('female') || 
                voice.name.includes('woman') || 
                voice.name.includes('girl')
            );
            
            if (femaleVoice) {
                speech.voice = femaleVoice;
            }
            
            speech.onend = function() {
                // Resume listening after speech completes only if call is still active
                if (callInProgress && !permissionDenied) {
                    updateCallStatus('Listening...');
                    startListening();
                }
            };
            
            window.speechSynthesis.speak(speech);
        } else {
            // If speech synthesis not available
            console.warn('Speech synthesis not supported');
            if (callInProgress && !permissionDenied) {
                updateCallStatus('Listening...');
                startListening();
            }
        }
    }
    
    /**
     * Generate speech using Piper TTS API
     */
    function generatePiperTTS(text) {
        updateCallStatus('Generating Piper TTS...');
        
        // Make API call to Piper TTS service
        fetch('/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                voice: 'en_US-amy-medium', // Specify the Piper voice to use
                provider: 'piper'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.audio_url) {
                updateCallStatus('Speaking with Piper voice...');
                speakWithAudio(data.audio_url);
            } else if (data.error && data.error.includes('API key')) {
                console.warn('Piper TTS API key not configured:', data.error);
                updateCallStatus('API key not configured. Using browser TTS...');
                speakText(text);
            } else {
                throw new Error(data.error || 'Failed to generate Piper TTS');
            }
        })
        .catch(error => {
            console.error('Error generating Piper TTS:', error);
            // Fall back to browser TTS as last resort
            updateCallStatus('Using browser TTS (fallback)...');
            speakText(text);
        });
    }
    
    /**
     * Play audio from server-generated TTS
     */
    function speakWithAudio(audioUrl) {
        const audio = new Audio(audioUrl);
        
        audio.onended = function() {
            // Resume listening after audio completes only if call is still active
            if (callInProgress && !permissionDenied) {
                updateCallStatus('Listening...');
                startListening();
            }
        };
        
        audio.onerror = function() {
            console.error('Error playing audio');
            updateCallStatus('Error playing audio');
            // Fall back to browser TTS
            speakText(sophiaResponseText.textContent);
        };
        
        audio.play().catch(error => {
            console.error('Error playing audio:', error);
            // Fall back to browser TTS
            speakText(sophiaResponseText.textContent);
        });
    }
    
    /**
     * Update the call status display
     */
    function updateCallStatus(status) {
        if (callStatus) {
            callStatus.textContent = status;
        }
    }
});
