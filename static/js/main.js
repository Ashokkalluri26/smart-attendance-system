document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const startButton = document.getElementById('start-camera');
    const takeAttendanceButton = document.getElementById('take-attendance');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'alert mt-3';
    messageDiv.style.display = 'none';
    video.parentElement.appendChild(messageDiv);
    let stream = null;

    // Check if getUserMedia is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support camera access. Please use a modern browser like Chrome or Firefox.');
        startButton.disabled = true;
        return;
    }

    startButton.addEventListener('click', async () => {
        try {
            // Request camera access with specific constraints
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            });
            
            // Attach stream to video element
            video.srcObject = stream;
            await video.play(); // Ensure video starts playing
            
            startButton.disabled = true;
            takeAttendanceButton.disabled = false;
            messageDiv.style.display = 'none';
            console.log('Camera started successfully');
        } catch (err) {
            console.error('Error accessing camera:', err);
            if (err.name === 'NotAllowedError') {
                alert('Camera access was denied. Please allow camera access and try again.');
            } else if (err.name === 'NotFoundError') {
                alert('No camera found. Please make sure your camera is connected and not in use by another application.');
            } else {
                alert('Error accessing camera: ' + err.message);
            }
        }
    });

    takeAttendanceButton.addEventListener('click', async () => {
        if (!stream) {
            alert('Camera not started. Please start the camera first.');
            return;
        }

        try {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Draw the current video frame
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Convert to blob
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob, 'attendance.jpg');

                try {
                    messageDiv.textContent = 'Processing...';
                    messageDiv.className = 'alert alert-info mt-3';
                    messageDiv.style.display = 'block';

                    const response = await fetch('/mark-attendance', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    if (result.success) {
                        messageDiv.textContent = result.message;
                        messageDiv.className = 'alert alert-success mt-3';
                        // Stop the camera after successful attendance
                        if (stream) {
                            stream.getTracks().forEach(track => track.stop());
                            video.srcObject = null;
                            startButton.disabled = false;
                            takeAttendanceButton.disabled = true;
                        }
                    } else {
                        messageDiv.textContent = result.message;
                        messageDiv.className = 'alert alert-danger mt-3';
                    }
                } catch (err) {
                    console.error('Error sending image to server:', err);
                    messageDiv.textContent = 'Error marking attendance. Please try again.';
                    messageDiv.className = 'alert alert-danger mt-3';
                }
            }, 'image/jpeg', 0.9);
        } catch (err) {
            console.error('Error capturing image:', err);
            messageDiv.textContent = 'Error capturing image. Please try again.';
            messageDiv.className = 'alert alert-danger mt-3';
        }
    });

    // Cleanup when leaving the page
    window.addEventListener('beforeunload', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
}); 