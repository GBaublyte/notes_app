/* static/js/script.js */
document.addEventListener("DOMContentLoaded", function() {
    console.log("Notes App JS Loaded!");

    // Example: Toggle note visibility (simple example)
    const toggleNoteButtons = document.querySelectorAll(".toggle-note");
    toggleNoteButtons.forEach(button => {
        button.addEventListener("click", function() {
            const noteContent = this.nextElementSibling;
            if (noteContent.style.display === "none") {
                noteContent.style.display = "block";
            } else {
                noteContent.style.display = "none";
            }
        });
    });
});