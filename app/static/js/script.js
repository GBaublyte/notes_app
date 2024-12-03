/* static/js/script.js */
     document.addEventListener("DOMContentLoaded", function() {
         console.log("Notes App JS Loaded!");

         // Add Login functionality
         async function login(username, password) {
             try {
                 const response = await fetch('/token', {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/x-www-form-urlencoded',
                     },
                     body: new URLSearchParams({
                         'username': username,
                         'password': password
                     })
                 });

                 if (response.ok) {
                     const result = await response.json();
                     console.log('Login successful:', result);
                     const loginContainer = document.getElementById('login-container');
                     if (loginContainer) {
                         loginContainer.innerHTML = `<p>Access Token: ${result.access_token}</p>`;
                     } else {
                         console.error('LoginContainer not found');
                     }
                 } else {
                     const errorData = await response.json();
                     console.error('Login failed:', errorData);
                     const errorMessage = document.getElementById('error-message');
                     if (errorMessage) {
                         errorMessage.textContent = "Login failed. Please try again.";
                     }
                 }
             } catch (error) {
                 console.error('An error occurred during login:', error);
                 const errorMessage = document.getElementById('error-message');
                 if (errorMessage) {
                     errorMessage.textContent = "An error occurred. Please try again.";
                 }
             }
         }

         // Attach event listener to login form or button
         const loginForm = document.getElementById('login-form');
         if (loginForm) {
             loginForm.addEventListener('submit', function(event) {
                 event.preventDefault();
                 const username = loginForm.querySelector('input[name="username"]').value;
                 const password = loginForm.querySelector('input[name="password"]').value;
                 login(username, password);
             });
         }
     });