function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("mainContent");
    const toggleBtn = document.querySelector(".toggle-btn");

    sidebar.classList.toggle("collapsed");
    mainContent.classList.toggle("expanded");
    toggleBtn.classList.toggle("move-left");
}

function showNewEntry() {
    var form = document.getElementById("newEntryForm");
    if (form) {
        form.style.display = form.style.display === "none" ? "block" : "none";
    }
}

/* 🎤 Voice Recording */
function startRecording() {
    if (!('webkitSpeechRecognition' in window)) {
        alert("Speech Recognition not supported in this browser. Use Chrome.");
        return;
    }

    const recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.start();

    recognition.onresult = function(event) {
        document.getElementById("content").value =
            event.results[0][0].transcript;
    };

    recognition.onerror = function(event) {
        alert("Error occurred in recognition: " + event.error);
    };
}