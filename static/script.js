const fileUpload = get("#file-upload")
const msgerForm = get(".msger-inputarea");
const msgerInput = get(".msger-input");
const msgerChat = get(".msger-chat");

// Icons from flaticon
const BOT_IMG = "https://cdn1.iconfinder.com/data/icons/ninja-things-1/1772/ninja-simple-512.png";  // Update to use a current icon URL if needed
const PERSON_IMG = "https://www.pinclipart.com/picdir/middle/205-2059398_blinkk-en-mac-app-store-ninja-icon-transparent.png";  // Update to use a current icon URL if needed
const BOT_NAME = "Helper Bot";
const PERSON_NAME = "User";


fileUpload.addEventListener('change', function(event) {
    const file = event.target.files[0];
    const fileDisplay = document.getElementById('file-display');

    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        // Upload the file to the server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.filename) {

                // Create file item container
                const fileItem = document.createElement('div');
                fileItem.classList.add('file-item');

                // File info section
                const fileInfo = document.createElement('div');
                fileInfo.classList.add('file-info');

                // File name
                const fileNameElement = document.createElement('span');
                fileNameElement.classList.add('file-name');
                fileNameElement.textContent = data.filename;

                // Append file name to info
                fileInfo.appendChild(fileNameElement);

                // File action buttons
                const fileActions = document.createElement('div');
                fileActions.classList.add('file-actions');

                // Preview button
                const previewBtn = document.createElement('span');
                previewBtn.classList.add('action-btn');
                previewBtn.innerHTML = '<i class="fa fa-eye"></i> Preview';
                previewBtn.title = 'Preview file';
                previewBtn.addEventListener('click', function() {
                    window.open('/uploads/' + data.filename, '_blank');
                });

                // Delete button
                const deleteBtn = document.createElement('span');
                deleteBtn.classList.add('action-btn', 'delete-btn');
                deleteBtn.innerHTML = '<i class="fa fa-trash"></i> Delete';
                deleteBtn.title = 'Delete file';
                deleteBtn.addEventListener('click', function() {
                    fetch('/delete/' + data.filename, { method: 'DELETE' })
                        .then(response => response.json())
                        .then(result => {
                            if (result.status === 'File deleted') {
                                fileItem.remove();
                                if (!fileDisplay.querySelector('.file-item')) {
                                    fileDisplay.innerHTML = '<p class="no-files">No files uploaded yet.</p>';
                                }
                            } else {
                                console.error('Error deleting file:', result.error);
                            }
                        })
                        .catch(error => {
                            console.error('Error deleting file:', error);
                        });
                });

                // Append action buttons
                fileActions.appendChild(previewBtn);

                // Append file info and actions to item
                fileItem.appendChild(fileInfo);
                fileItem.appendChild(fileActions);

                // Add item to display section
                fileDisplay.appendChild(fileItem);
            }
        })
        .catch(error => {
            console.error('Error uploading file:', error);
        });
    }
});




msgerForm.addEventListener("submit", event => {
    event.preventDefault();

    const msgText = msgerInput.value;
    if (!msgText) return;

    appendMessage(PERSON_NAME, PERSON_IMG, "right", msgText);
    msgerInput.value = "";

    // Here you can replace `botResponse()` with a custom function that calls your Python backend
    // botResponse();
    fetchBotResponse(msgText);
});


function appendMessage(name, img, side, text) {
    const msgHTML = `
                <div class="msg ${side}-msg">
                    <div class="msg-img" style="background-image: url(${img})"></div>
    
                    <div class="msg-bubble">
                        <div class="msg-info">
                            <div class="msg-info-name">${name}</div>
                            <div class="msg-info-time">${formatDate(new Date())}</div>
                        </div>
    
                        <div class="msg-text">${text}</div>
                    </div>
                </div>
            `;

    msgerChat.insertAdjacentHTML("beforeend", msgHTML);
    msgerChat.scrollTop += 500;
}


function botResponse() {
    const r = random(0, BOT_MSGS.length - 1);
    const msgText = BOT_MSGS[r];
    const delay = msgText.split(" ").length * 100;

    setTimeout(() => {
        appendMessage(BOT_NAME, BOT_IMG, "left", msgText);
    }, delay);
}

// Utility functions
function get(selector, root = document) {
    return root.querySelector(selector);
}

function formatDate(date) {
    const h = "0" + date.getHours();
    const m = "0" + date.getMinutes();
    return `${h.slice(-2)}:${m.slice(-2)}`;
}

function random(min, max) {
    return Math.floor(Math.random() * (max - min) + min);
}

// New function to fetch data from Python backend
async function fetchBotResponse(userMessage) {
    var start = new Date().getTime();
    try {
        const response = await fetch('http://127.0.0.1:7654/api/question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userMessage, user_id: "User" })
        });

        const data = await response.json();
        appendMessage(BOT_NAME, BOT_IMG, "left", data.reply);
    } catch (error) {
        console.error('Error fetching data:', error);
        appendMessage(BOT_NAME, BOT_IMG, "left", "Sorry, I couldn't reach the server.");
    }
    var end = new Date().getTime();
    var time = (end - start) / 1000;
    console.log('Execution time: ' + time);
}
