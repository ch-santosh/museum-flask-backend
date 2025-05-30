from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
import os
from datetime import datetime, timedelta
import logging
import qrcode
import base64
import io
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable for Firebase client
db = None

# Create templates directory and index.html before app initialization
def setup_directories():
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Create index.html with enhanced styling
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Athena Museum Payment Portal</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --accent-color: #4facfe;
            --success-color: #00d4aa;
            --error-color: #ff6b6b;
            --warning-color: #feca57;
            --dark-bg: #0a0a0a;
            --card-bg: rgba(255, 255, 255, 0.05);
            --glass-bg: rgba(255, 255, 255, 0.1);
            --border-color: rgba(102, 126, 234, 0.3);
            --text-primary: #ffffff;
            --text-secondary: #b8c6db;
            --shadow-glow: 0 0 30px rgba(102, 126, 234, 0.3);
        }

        body {
            font-family: 'Exo 2', sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow-x: hidden;
            position: relative;
        }

        /* Animated Background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            background: 
                radial-gradient(circle at 20% 80%, rgba(102, 126, 234, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(118, 75, 162, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(79, 172, 254, 0.1) 0%, transparent 50%);
            animation: bgShift 20s ease-in-out infinite;
        }

        @keyframes bgShift {
            0%, 100% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.1) rotate(180deg); }
        }

        /* Floating Particles */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            pointer-events: none;
        }

        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--primary-color);
            border-radius: 50%;
            opacity: 0.6;
            animation: float 15s infinite linear;
        }

        @keyframes float {
            0% {
                transform: translateY(100vh) translateX(0) scale(0);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) translateX(100px) scale(1);
                opacity: 0;
            }
        }

        /* Back Button */
        .back-btn {
            position: fixed;
            top: 30px;
            left: 30px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            z-index: 1000;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-glow);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .back-btn:hover {
            transform: translateY(-5px) scale(1.1);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5);
        }

        .back-btn:active {
            transform: translateY(-2px) scale(1.05);
        }

        /* Main Container */
        .container {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-radius: 25px;
            padding: 3rem;
            max-width: 500px;
            width: 90%;
            box-shadow: 
                var(--shadow-glow),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
            animation: containerEntry 1s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes containerEntry {
            0% {
                opacity: 0;
                transform: translateY(50px) scale(0.9);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.03), transparent);
            pointer-events: none;
            animation: shimmer 3s ease-in-out infinite;
        }

        @keyframes shimmer {
            0%, 100% { opacity: 0; }
            50% { opacity: 1; }
        }

        /* Title */
        .title {
            font-family: 'Orbitron', monospace;
            font-size: 2.5rem;
            font-weight: 900;
            text-align: center;
            margin-bottom: 2rem;
            background: linear-gradient(45deg, var(--primary-color), var(--accent-color), var(--secondary-color));
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientFlow 4s ease-in-out infinite;
            text-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
        }

        @keyframes gradientFlow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        .subtitle {
            text-align: center;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            font-size: 1.1rem;
            font-weight: 300;
        }

        /* Form Styles */
        .form-group {
            margin-bottom: 1.5rem;
            position: relative;
        }

        .form-label {
            display: block;
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .form-input {
            width: 100%;
            padding: 1rem 1.5rem;
            background: var(--glass-bg);
            border: 2px solid var(--border-color);
            border-radius: 15px;
            color: var(--text-primary);
            font-size: 1rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .form-input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
            background: rgba(255, 255, 255, 0.15);
        }

        .form-input::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }

        /* Button Styles */
        .btn {
            width: 100%;
            padding: 1rem 2rem;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: none;
            border-radius: 15px;
            color: white;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.6);
        }

        .btn:active {
            transform: translateY(-1px);
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s ease;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Loading Spinner */
        .spinner {
            display: none;
            width: 40px;
            height: 40px;
            margin: 1rem auto;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-left: 4px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Alert Messages */
        .alert {
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            font-weight: 500;
            animation: alertSlide 0.3s ease;
        }

        @keyframes alertSlide {
            0% {
                opacity: 0;
                transform: translateY(-10px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .alert-error {
            background: rgba(255, 107, 107, 0.1);
            border: 1px solid var(--error-color);
            color: var(--error-color);
        }

        .alert-success {
            background: rgba(0, 212, 170, 0.1);
            border: 1px solid var(--success-color);
            color: var(--success-color);
        }

        /* Ticket Display */
        .ticket-card {
            background: var(--glass-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(15px);
            position: relative;
            overflow: hidden;
            animation: ticketEntry 0.5s ease;
        }

        @keyframes ticketEntry {
            0% {
                opacity: 0;
                transform: scale(0.9) rotateY(10deg);
            }
            100% {
                opacity: 1;
                transform: scale(1) rotateY(0deg);
            }
        }

        .ticket-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .ticket-title {
            font-family: 'Orbitron', monospace;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }

        .ticket-detail {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .ticket-detail:last-child {
            border-bottom: none;
        }

        .ticket-label {
            color: var(--text-secondary);
            font-weight: 500;
        }

        .ticket-value {
            color: var(--text-primary);
            font-weight: 600;
        }

        /* QR Code Container */
        .qr-container {
            text-align: center;
            background: var(--glass-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            backdrop-filter: blur(15px);
            position: relative;
        }

        .qr-code {
            display: inline-block;
            padding: 1rem;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            animation: qrPulse 2s ease-in-out infinite;
        }

        @keyframes qrPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .qr-code img {
            display: block;
            max-width: 200px;
            height: auto;
        }

        .hash-display {
            font-family: 'Courier New', monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            color: var(--accent-color);
            font-size: 0.9rem;
            margin-top: 1rem;
            word-break: break-all;
        }

        /* Success Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 2000;
            backdrop-filter: blur(5px);
        }

        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 25px;
            padding: 3rem;
            max-width: 500px;
            width: 90%;
            text-align: center;
            backdrop-filter: blur(20px);
            animation: modalEntry 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes modalEntry {
            0% {
                opacity: 0;
                transform: translate(-50%, -50%) scale(0.8);
            }
            100% {
                opacity: 1;
                transform: translate(-50%, -50%) scale(1);
            }
        }

        .success-icon {
            font-size: 4rem;
            color: var(--success-color);
            margin-bottom: 1rem;
            animation: successBounce 0.6s ease;
        }

        @keyframes successBounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }

        /* Confetti */
        .confetti {
            position: absolute;
            width: 10px;
            height: 10px;
            background: var(--primary-color);
            animation: confettiFall 3s linear infinite;
        }

        @keyframes confettiFall {
            0% {
                transform: translateY(-100vh) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(100vh) rotate(360deg);
                opacity: 0;
            }
        }

        /* Validity Badge */
        .validity-badge {
            display: inline-block;
            background: linear-gradient(135deg, var(--success-color), #00b894);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-top: 1rem;
            animation: validityPulse 2s ease-in-out infinite;
        }

        @keyframes validityPulse {
            0%, 100% { box-shadow: 0 0 10px rgba(0, 212, 170, 0.3); }
            50% { box-shadow: 0 0 20px rgba(0, 212, 170, 0.6); }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 2rem;
                margin: 1rem;
            }
            
            .title {
                font-size: 2rem;
            }
            
            .back-btn {
                top: 20px;
                left: 20px;
                width: 50px;
                height: 50px;
                font-size: 1.2rem;
            }
        }

        /* Hide elements initially */
        .hidden {
            display: none !important;
        }

        /* Booking ID highlight */
        .booking-id {
            font-family: 'Orbitron', monospace;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--accent-color);
            text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
        }
    </style>
</head>
<body>
    <!-- Animated Background -->
    <div class="bg-animation"></div>
    
    <!-- Floating Particles -->
    <div class="particles" id="particles"></div>
    
    <!-- Back Button -->
    <button class="back-btn" onclick="goBack()">
        <i class="fas fa-arrow-left"></i>
    </button>
    
    <!-- Main Container -->
    <div class="container">
        <h1 class="title">ATHENA</h1>
        <p class="subtitle">Museum Payment Portal</p>
        
        <!-- Email Validation Form -->
        <div id="email-form">
            <div class="form-group">
                <label class="form-label" for="email">
                    <i class="fas fa-envelope"></i> Email Address
                </label>
                <input type="email" id="email" class="form-input" placeholder="Enter your booking email" required>
            </div>
            
            <div id="email-error" class="alert alert-error hidden"></div>
            
            <button id="validate-btn" class="btn">
                <i class="fas fa-search"></i> Validate Booking
            </button>
            
            <div class="spinner" id="validate-spinner"></div>
        </div>
        
        <!-- Booking Details -->
        <div id="booking-details" class="hidden">
            <div class="ticket-card">
                <div class="ticket-header">
                    <div class="ticket-title">Booking Confirmed</div>
                    <div class="booking-id" id="display-booking-id"></div>
                </div>
                
                <div class="ticket-detail">
                    <span class="ticket-label">Email:</span>
                    <span class="ticket-value" id="display-email"></span>
                </div>
                
                <div class="ticket-detail">
                    <span class="ticket-label">Phone:</span>
                    <span class="ticket-value" id="display-phone"></span>
                </div>
                
                <div class="ticket-detail">
                    <span class="ticket-label">Tickets:</span>
                    <span class="ticket-value" id="display-tickets"></span>
                </div>
                
                <div class="ticket-detail">
                    <span class="ticket-label">Amount:</span>
                    <span class="ticket-value" id="display-amount"></span>
                </div>
                
                <div class="ticket-detail">
                    <span class="ticket-label">Validity:</span>
                    <span class="ticket-value" id="display-validity"></span>
                </div>
            </div>
            
            <button id="payment-btn" class="btn">
                <i class="fas fa-credit-card"></i> Process Payment
            </button>
            
            <div class="spinner" id="payment-spinner"></div>
        </div>
    </div>
    
    <!-- Success Modal -->
    <div id="success-modal" class="modal">
        <div class="modal-content">
            <div class="success-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <h2 style="color: var(--success-color); margin-bottom: 1rem;">Payment Successful!</h2>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">Your booking has been confirmed and tickets are ready!</p>
            
            <div class="qr-container">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">Your Entry QR Code</h3>
                <div class="qr-code" id="qr-display"></div>
                <div class="hash-display" id="hash-display"></div>
                <div class="validity-badge">
                    Valid for 1 day from booking
                </div>
            </div>
            
            <p style="color: var(--text-secondary); margin: 1rem 0;">A confirmation email with your QR code has been sent.</p>
            
            <button class="btn" onclick="closeModal()">
                <i class="fas fa-home"></i> Return to Booking
            </button>
        </div>
    </div>
    
    <script>
        // Create floating particles
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            const particleCount = 50;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 15 + 's';
                particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
                
                // Random colors
                const colors = ['#667eea', '#764ba2', '#4facfe', '#00f2fe'];
                particle.style.background = colors[Math.floor(Math.random() * colors.length)];
                
                particlesContainer.appendChild(particle);
            }
        }
        
        // Create confetti effect
        function createConfetti() {
            const colors = ['#667eea', '#764ba2', '#4facfe', '#00f2fe', '#00d4aa'];
            const confettiCount = 100;
            
            for (let i = 0; i < confettiCount; i++) {
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + '%';
                confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.animationDelay = Math.random() * 3 + 's';
                confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
                
                document.body.appendChild(confetti);
                
                // Remove confetti after animation
                setTimeout(() => {
                    confetti.remove();
                }, 5000);
            }
        }
        
        // Format validity date
        function formatValidity(validityDate) {
            if (!validityDate) return '1 day from booking';
            
            const date = new Date(validityDate);
            const now = new Date();
            const diffTime = date - now;
            const diffHours = Math.ceil(diffTime / (1000 * 60 * 60));
            
            if (diffHours > 0) {
                if (diffHours > 24) {
                    const diffDays = Math.ceil(diffHours / 24);
                    return `${diffDays} day${diffDays > 1 ? 's' : ''} remaining`;
                }
                return `${diffHours} hour${diffHours > 1 ? 's' : ''} remaining`;
            } else {
                return 'Expired';
            }
        }
        
        // Go back to Streamlit
        function goBack() {
            window.location.href = 'http://localhost:8501';
        }
        
        // Close success modal
        function closeModal() {
            document.getElementById('success-modal').style.display = 'none';
            // Redirect back to Streamlit
            setTimeout(() => {
                goBack();
            }, 500);
        }
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            createParticles();
            
            // Auto-fill email from URL parameter
            const urlParams = new URLSearchParams(window.location.search);
            const emailParam = urlParams.get('email');
            
            if (emailParam) {
                document.getElementById('email').value = emailParam;
                // Auto-validate after a short delay
                setTimeout(() => {
                    document.getElementById('validate-btn').click();
                }, 1000);
            }
            
            // Email validation
            document.getElementById('validate-btn').addEventListener('click', function() {
                const email = document.getElementById('email').value;
                const errorDiv = document.getElementById('email-error');
                const spinner = document.getElementById('validate-spinner');
                const button = this;
                
                if (!email) {
                    errorDiv.textContent = 'Please enter your email address';
                    errorDiv.classList.remove('hidden');
                    return;
                }
                
                errorDiv.classList.add('hidden');
                spinner.style.display = 'block';
                button.disabled = true;
                
                fetch('/validate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `email=${encodeURIComponent(email)}`
                })
                .then(response => response.json())
                .then(data => {
                    spinner.style.display = 'none';
                    button.disabled = false;
                    
                    if (data.success) {
                        // Hide email form and show booking details
                        document.getElementById('email-form').classList.add('hidden');
                        document.getElementById('booking-details').classList.remove('hidden');
                        
                        // Populate booking details
                        document.getElementById('display-booking-id').textContent = data.booking_id || 'Pending';
                        document.getElementById('display-email').textContent = data.email;
                        document.getElementById('display-phone').textContent = data.phone;
                        document.getElementById('display-tickets').textContent = data.tickets;
                        document.getElementById('display-amount').textContent = `₹${data.amount}`;
                        
                        // Format and display validity
                        document.getElementById('display-validity').textContent = formatValidity(data.validity);
                    } else {
                        errorDiv.textContent = data.message;
                        errorDiv.classList.remove('hidden');
                    }
                })
                .catch(error => {
                    spinner.style.display = 'none';
                    button.disabled = false;
                    errorDiv.textContent = 'An error occurred. Please try again.';
                    errorDiv.classList.remove('hidden');
                    console.error('Error:', error);
                });
            });
            
            // Payment processing
            document.getElementById('payment-btn').addEventListener('click', function() {
                const spinner = document.getElementById('payment-spinner');
                const button = this;
                
                spinner.style.display = 'block';
                button.disabled = true;
                
                fetch('/payment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    spinner.style.display = 'none';
                    
                    if (data.success) {
                        // Show success modal
                        const modal = document.getElementById('success-modal');
                        const qrDisplay = document.getElementById('qr-display');
                        const hashDisplay = document.getElementById('hash-display');
                        
                        qrDisplay.innerHTML = `<img src="data:image/png;base64,${data.qr_code}" alt="QR Code">`;
                        hashDisplay.textContent = data.hash;
                        
                        modal.style.display = 'block';
                        createConfetti();
                    } else {
                        alert(data.message);
                        button.disabled = false;
                    }
                })
                .catch(error => {
                    spinner.style.display = 'none';
                    button.disabled = false;
                    alert('An error occurred. Please try again.');
                    console.error('Error:', error);
                });
            });
        });
    </script>
</body>
</html>
""")
    
    logger.info("Templates and static directories created successfully")
    return "Setup completed successfully"

# Replace the init_firebase function in your app.py with this:
def init_firebase():
    global db
    try:
        if not firebase_admin._apps:
            # Check if all required environment variables are present
            required_vars = [
                'FIREBASE_PROJECT_ID',
                'FIREBASE_PRIVATE_KEY_ID', 
                'FIREBASE_PRIVATE_KEY',
                'FIREBASE_CLIENT_EMAIL',
                'FIREBASE_CLIENT_ID',
                'FIREBASE_CLIENT_X509_CERT_URL'
            ]
            
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                logger.error(f"Missing environment variables: {missing_vars}")
                return None
            
            firebase_config = {
                "type": "service_account",
                "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
                "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.environ.get('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_X509_CERT_URL'),
                "universe_domain": "googleapis.com"
            }
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase initialized successfully")
        return db
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        return None
# Run setup before initializing the app
setup_directories()

app = Flask(__name__)
app.secret_key = "athena_museum_secret_key_2024"

# Initialize Firebase when the app starts
with app.app_context():
    init_firebase()

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "adhilsk201@gmail.com"
SMTP_PASSWORD = "qemt ymquxttc smor"

# Helper functions
def get_booking_by_email(email):
    """Retrieve booking information from Firebase by email"""
    try:
        global db
        if not db:
            db = init_firebase()
        
        bookings = db.collection('bookings').where('email', '==', email).order_by('created_at', direction=firestore.Query.DESCENDING).limit(1).get()
        
        if bookings:
            booking_data = bookings[0].to_dict()
            booking_data['doc_id'] = bookings[0].id
            return booking_data
        return None
    except Exception as e:
        logger.error(f"Error retrieving booking: {str(e)}")
        return None

def update_booking_status(doc_id, status, hash_code=None, booking_id_str=None):
    """Update booking status in Firebase"""
    try:
        global db
        if not db:
            db = init_firebase()
            
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        
        if hash_code:
            update_data["hash"] = hash_code
            
        if booking_id_str:
            update_data["booking_id"] = booking_id_str
            
        db.collection('bookings').document(doc_id).update(update_data)
        logger.info(f"Booking status updated: {update_data}")
        return True
    except Exception as e:
        logger.error(f"Error updating booking status: {str(e)}")
        return False

def add_to_payments(booking_id, email, amount):
    """Add payment record to Firebase payments collection"""
    try:
        global db
        if not db:
            db = init_firebase()
            
        payment_data = {
            "booking_id": booking_id,
            "email": email,
            "amount": amount,
            "payment_date": datetime.now(),
            "status": "completed"
        }
        db.collection('payments').add(payment_data)
        logger.info(f"Payment added: {payment_data}")
        return True
    except Exception as e:
        logger.error(f"Error adding payment: {str(e)}")
        return False

def generate_qr_code(booking_id):
    """Generate QR code for booking confirmation with hash value"""
    try:
        # Create a unique hash based on booking ID and timestamp
        hash_string = hashlib.sha256(f"{booking_id}-{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        # Create QR code with the hash
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"ATHENA-MUSEUM-{booking_id}-{hash_string}")
        qr.make(fit=True)
        
        # Create an image from the QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to a bytes buffer
        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)
        
        # Convert to base64 for embedding
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return qr_base64, hash_string
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return None, None

def send_confirmation_email(email, booking_details, booking_id, qr_code, hash_string):
    """Send confirmation email with QR code"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "🎫 Your Athena Museum Booking Confirmation"
        
        validity_date = (datetime.now() + timedelta(days=1)).strftime('%d %b %Y, %H:%M')
        
        # Enhanced email body
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 2.5rem; font-weight: 700; }}
                .header p {{ margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9; }}
                .content {{ padding: 40px 30px; }}
                .ticket-card {{ background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px; padding: 30px; margin: 30px 0; border-left: 5px solid #667eea; }}
                .ticket-detail {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #dee2e6; }}
                .ticket-detail:last-child {{ border-bottom: none; }}
                .label {{ font-weight: 600; color: #495057; }}
                .value {{ font-weight: 700; color: #212529; }}
                .qr-section {{ text-align: center; background: #f8f9fa; border-radius: 15px; padding: 30px; margin: 30px 0; }}
                .qr-code {{ display: inline-block; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                .hash-code {{ font-family: 'Courier New', monospace; background: #e9ecef; padding: 10px; border-radius: 5px; margin: 15px 0; font-size: 0.9rem; color: #495057; }}
                .validity-badge {{ display: inline-block; background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 10px 20px; border-radius: 25px; font-weight: 600; margin: 15px 0; }}
                .footer {{ background: #f8f9fa; padding: 30px; text-align: center; color: #6c757d; }}
                .instructions {{ background: #e3f2fd; border-radius: 10px; padding: 20px; margin: 20px 0; }}
                .instructions h3 {{ color: #1976d2; margin-top: 0; }}
                .instructions ul {{ margin: 10px 0; padding-left: 20px; }}
                .instructions li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏛️ ATHENA MUSEUM</h1>
                    <p>Your Booking is Confirmed!</p>
                </div>
                
                <div class="content">
                    <p>Dear Valued Visitor,</p>
                    <p>Congratulations! Your payment has been successfully processed and your booking for the Athena Museum of Science and Technology is now confirmed.</p>
                    
                    <div class="ticket-card">
                        <h2 style="color: #667eea; margin-top: 0;">🎫 Booking Details</h2>
                        <div class="ticket-detail">
                            <span class="label">Booking ID:</span>
                            <span class="value">{booking_id}</span>
                        </div>
                        <div class="ticket-detail">
                            <span class="label">Email:</span>
                            <span class="value">{email}</span>
                        </div>
                        <div class="ticket-detail">
                            <span class="label">Phone:</span>
                            <span class="value">{booking_details.get('phone', 'N/A')}</span>
                        </div>
                        <div class="ticket-detail">
                            <span class="label">Number of Tickets:</span>
                            <span class="value">{booking_details.get('tickets', 'N/A')}</span>
                        </div>
                        <div class="ticket-detail">
                            <span class="label">Total Amount:</span>
                            <span class="value">₹{booking_details.get('amount', 'N/A')}</span>
                        </div>
                        <div class="ticket-detail">
                            <span class="label">Booking Date:</span>
                            <span class="value">{datetime.now().strftime('%d %b %Y, %H:%M')}</span>
                        </div>
                    </div>
                    
                    <div class="qr-section">
                        <h3 style="color: #667eea; margin-bottom: 20px;">📱 Your Entry QR Code</h3>
                        <p>Present this QR code at the museum entrance for quick entry:</p>
                        <div class="qr-code">
                            <img src="data:image/png;base64,{qr_code}" alt="QR Code" style="width: 200px; height: 200px;">
                        </div>
                        <div class="hash-code">
                            <strong>Security Hash:</strong> {hash_string}
                        </div>
                        <div class="validity-badge">
                            ✅ Valid until: {validity_date}
                        </div>
                    </div>
                    
                    <div class="instructions">
                        <h3>📋 Important Instructions</h3>
                        <ul>
                            <li><strong>Arrival:</strong> Please arrive 15 minutes before your preferred time</li>
                            <li><strong>Entry:</strong> Show your QR code at the entrance for scanning</li>
                            <li><strong>Validity:</strong> Your ticket is valid for 1 day from booking time</li>
                            <li><strong>Contact:</strong> For any queries, call +91 22 1234 5678</li>
                            <li><strong>Exhibitions:</strong> Access to all current exhibitions included</li>
                        </ul>
                    </div>
                    
                    <p><strong>What to expect at the museum:</strong></p>
                    <ul>
                        <li>🤖 <strong>AI Revolution</strong> - Explore the future of artificial intelligence</li>
                        <li>🚀 <strong>Space Odyssey</strong> - Journey through the cosmos</li>
                        <li>⚛️ <strong>Quantum Realm</strong> - Discover quantum physics mysteries</li>
                    </ul>
                    
                    <p>We're excited to welcome you to the Athena Museum and hope you have an amazing experience exploring science and technology!</p>
                </div>
                
                <div class="footer">
                    <p><strong>Athena Museum of Science and Technology</strong></p>
                    <p>📍 123 Science Avenue, Mumbai, Maharashtra 400001, India</p>
                    <p>📞 +91 22 1234 5678 | 📧 info@athenamuseum.com</p>
                    <p>🌐 www.athenamuseum.com</p>
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #dee2e6;">
                    <p style="font-size: 0.9rem; color: #6c757d;">
                        This is an automated confirmation email. Please do not reply to this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Confirmation email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending confirmation email: {str(e)}")
        return False

# Routes
@app.route("/", methods=["GET"])
def index():
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return f"Error: {str(e)}", 500

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "message": "Athena Museum Payment Portal is running"}, 200

@app.route("/validate", methods=["POST"])
def validate():
    if request.method == "POST":
        email = request.form.get("email")
        
        if not email:
            return jsonify({
                "success": False,
                "message": "Email is required."
            })
        
        # Get booking details from Firebase
        booking = get_booking_by_email(email)
        
        if booking:
            # Store data in session
            session['email'] = email
            session['tickets'] = booking.get('tickets', 0)
            session['amount'] = booking.get('amount', 0)
            session['phone'] = booking.get('phone', '')
            session['doc_id'] = booking.get('doc_id', '')
            session['booking_id'] = booking.get('booking_id', '')
            session['validity'] = booking.get('validity')
            
            return jsonify({
                "success": True,
                "email": email,
                "tickets": booking.get('tickets', 0),
                "amount": booking.get('amount', 0),
                "phone": booking.get('phone', ''),
                "booking_id": booking.get('booking_id', 'Pending'),
                "validity": booking.get('validity').isoformat() if booking.get('validity') else None
            })
        else:
            return jsonify({
                "success": False,
                "message": "No booking found for this email. Please book tickets first through our chatbot."
            })

@app.route("/payment", methods=["POST"])
def payment():
    if request.method == "POST":
        # Get data from session
        email = session.get('email')
        tickets = session.get('tickets', 0)
        amount = session.get('amount', 0)
        phone = session.get('phone', '')
        doc_id = session.get('doc_id', '')
        
        if not email or tickets <= 0:
            return jsonify({
                "success": False,
                "message": "Invalid session data. Please validate your email first."
            })
        
        # Generate a unique booking ID for the user
        booking_id = f"ATH{int(datetime.now().timestamp())}{tickets:02d}"
        
        # Generate QR code with hash
        qr_code, hash_string = generate_qr_code(booking_id)
        
        if qr_code and hash_string:
            # Update booking status in Firebase
            update_success = update_booking_status(
                doc_id, 
                "completed", 
                hash_string, 
                booking_id
            )
            
            # Add payment record to Firebase
            payment_success = add_to_payments(booking_id, email, amount)
            
            if update_success and payment_success:
                # Get booking details for email
                booking_details = {
                    'phone': phone,
                    'tickets': tickets,
                    'amount': amount
                }
                
                # Send confirmation email with QR code
                email_sent = send_confirmation_email(email, booking_details, booking_id, qr_code, hash_string)
                
                # Clear session data
                session.clear()
                
                return jsonify({
                    "success": True,
                    "booking_id": booking_id,
                    "qr_code": qr_code,
                    "hash": hash_string,
                    "message": f"Payment successful! Your booking ID is {booking_id}."
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Failed to update booking status. Please try again or contact support."
                })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to generate QR code. Please try again or contact support."
            })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Page not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Run the app
# Production configuration
def create_app():
    """Application factory pattern for production"""
    return app

# For Gunicorn
application = create_app()

# Remove this entire section at the bottom of your app.py:
# if __name__ == "__main__":
#     import os
#     port = int(os.environ.get('PORT', 8080))
#     debug = os.environ.get('FLASK_ENV') == 'development'
#     
#     print("🏛️ Athena Museum Payment Portal is starting...")
#     print(f"✨ Running on port: {port}")
#     print("🔗 Integration: Firebase Firestore, SMTP email, Streamlit chatbot")
#     
#     # Use Gunicorn in production, Flask dev server locally
#     if os.environ.get('RAILWAY_ENVIRONMENT'):
#         # Production - let Railway handle this
#         pass
#     else:
#         # Local development
#         app.run(debug=debug, host='0.0.0.0', port=port)

# Replace with this simple version:
if __name__ == "__main__":
    app.run(debug=True)