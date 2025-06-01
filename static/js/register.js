document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startButton = document.getElementById('start-camera');
    const captureButton = document.getElementById('capture');
    const submitButton = document.querySelector('button[type="submit"]');
    const form = document.getElementById('registration-form');
    let stream = null;
    let capturedImage = null;

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
            captureButton.disabled = false;
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

    captureButton.addEventListener('click', () => {
        if (!stream) {
            alert('Camera not started. Please start the camera first.');
            return;
        }

        try {
            // Make sure video dimensions are set
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Draw the current video frame
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert to base64
            capturedImage = canvas.toDataURL('image/jpeg', 0.9);
            
            // Stop the camera stream
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
            
            // Show the captured image
            video.style.display = 'none';
            canvas.style.display = 'block';
            submitButton.disabled = false;
            
            console.log('Image captured successfully');
        } catch (err) {
            console.error('Error capturing image:', err);
            alert('Error capturing image. Please try again.');
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!capturedImage) {
            alert('Please capture a photo first');
            return;
        }

        const formData = new FormData();
        formData.append('name', document.getElementById('name').value);
        formData.append('id', document.getElementById('id').value);

        // Convert base64 to blob
        try {
            const response = await fetch(capturedImage);
            const blob = await response.blob();
            formData.append('image', blob, 'registration.jpg');

            const serverResponse = await fetch('/register', {
                method: 'POST',
                body: formData
            });

            const result = await serverResponse.json();
            if (result.success) {
                alert('User registered successfully!');
                window.location.href = '/';
            } else {
                alert('Failed to register user: ' + result.message);
            }
        } catch (err) {
            console.error('Error registering user:', err);
            alert('Error registering user. Please try again.');
        }
    });

    // Cleanup when leaving the page
    window.addEventListener('beforeunload', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
}); 