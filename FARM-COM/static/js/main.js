// FarmCom Main JavaScript - Frontend functionality for farming equipment rental platform

// Global variables
let currentUser = null;
let equipmentData = [];
let marketplaceData = [];

// DOM Content Loaded Event
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadUserSession();
});

// Initialize the application
function initializeApp() {
    console.log('FarmCom App Initialized');
    
    // Check current page and load appropriate content
    const currentPage = window.location.pathname;
    
    switch(currentPage) {
        case '/dashboard':
            loadDashboard();
            break;
        case '/rent_equipment':
            loadRentEquipment();
            break;
        case '/rent_listings':
            loadRentListings();
            break;
        case '/buy_items':
            loadBuyItems();
            break;
        case '/marketplace':
            loadMarketplace();
            break;
        default:
            loadHomePage();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Navigation menu toggle (mobile)
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Search functionality
    const searchBtn = document.querySelector('#search-btn');
    const searchInput = document.querySelector('#search-input');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', performSearch);
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
    
    // Form submissions
    setupFormHandlers();
    
    // Modal handlers
    setupModalHandlers();
    
    // Filter handlers
    setupFilterHandlers();
}

// Load user session
function loadUserSession() {
    // Check if user is logged in (assuming session storage or local storage)
    const userData = sessionStorage.getItem('user');
    if (userData) {
        currentUser = JSON.parse(userData);
        updateUIForLoggedInUser();
    }
}

// Update UI for logged in user
function updateUIForLoggedInUser() {
    const loginBtn = document.querySelector('#login-btn');
    const userProfile = document.querySelector('#user-profile');
    
    if (loginBtn && userProfile && currentUser) {
        loginBtn.style.display = 'none';
        userProfile.style.display = 'block';
        userProfile.querySelector('.username').textContent = currentUser.name;
    }
}

// Dashboard functionality
function loadDashboard() {
    fetchUserRentals();
    fetchUserListings();
    fetchUserMessages();
    updateDashboardStats();
}

function fetchUserRentals() {
    fetch('/api/user/rentals')
        .then(response => response.json())
        .then(data => {
            displayUserRentals(data);
        })
        .catch(error => {
            console.error('Error fetching user rentals:', error);
            showNotification('Error loading rentals', 'error');
        });
}

function fetchUserListings() {
    fetch('/api/user/listings')
        .then(response => response.json())
        .then(data => {
            displayUserListings(data);
        })
        .catch(error => {
            console.error('Error fetching user listings:', error);
        });
}

function displayUserRentals(rentals) {
    const container = document.querySelector('#user-rentals');
    if (!container) return;
    
    container.innerHTML = '';
    
    rentals.forEach(rental => {
        const rentalCard = createRentalCard(rental);
        container.appendChild(rentalCard);
    });
}

function displayUserListings(listings) {
    const container = document.querySelector('#user-listings');
    if (!container) return;
    
    container.innerHTML = '';
    
    listings.forEach(listing => {
        const listingCard = createListingCard(listing);
        container.appendChild(listingCard);
    });
}

// Equipment rental functionality
function loadRentEquipment() {
    fetchEquipmentCategories();
    fetchFeaturedEquipment();
}

function fetchEquipmentCategories() {
    fetch('/api/equipment/categories')
        .then(response => response.json())
        .then(data => {
            displayEquipmentCategories(data);
        })
        .catch(error => {
            console.error('Error fetching equipment categories:', error);
        });
}

function fetchFeaturedEquipment() {
    fetch('/api/equipment/featured')
        .then(response => response.json())
        .then(data => {
            equipmentData = data;
            displayEquipmentGrid(data);
        })
        .catch(error => {
            console.error('Error fetching featured equipment:', error);
        });
}

function displayEquipmentGrid(equipment) {
    const container = document.querySelector('#equipment-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    equipment.forEach(item => {
        const equipmentCard = createEquipmentCard(item);
        container.appendChild(equipmentCard);
    });
}

function createEquipmentCard(equipment) {
    const card = document.createElement('div');
    card.className = 'equipment-card';
    card.innerHTML = `
        <div class="equipment-image">
            <img src="${equipment.image || '/static/images/equipment-placeholder.jpg'}" alt="${equipment.name}">
        </div>
        <div class="equipment-info">
            <h3>${equipment.name}</h3>
            <p class="equipment-description">${equipment.description}</p>
            <div class="equipment-details">
                <span class="price">₹${equipment.price_per_day}/day</span>
                <span class="location">${equipment.location}</span>
            </div>
            <div class="equipment-actions">
                <button class="btn btn-primary" onclick="rentEquipment(${equipment.id})">Rent Now</button>
                <button class="btn btn-secondary" onclick="viewEquipmentDetails(${equipment.id})">View Details</button>
            </div>
        </div>
    `;
    
    return card;
}

function rentEquipment(equipmentId) {
    if (!currentUser) {
        showLoginModal();
        return;
    }
    
    const equipment = equipmentData.find(item => item.id === equipmentId);
    if (!equipment) return;
    
    showRentModal(equipment);
}

function viewEquipmentDetails(equipmentId) {
    const equipment = equipmentData.find(item => item.id === equipmentId);
    if (!equipment) return;
    
    showEquipmentDetailsModal(equipment);
}

// Marketplace functionality
function loadMarketplace() {
    fetchMarketplaceItems();
    fetchMarketplaceCategories();
}

function fetchMarketplaceItems() {
    fetch('/api/marketplace/items')
        .then(response => response.json())
        .then(data => {
            marketplaceData = data;
            displayMarketplaceGrid(data);
        })
        .catch(error => {
            console.error('Error fetching marketplace items:', error);
        });
}

function displayMarketplaceGrid(items) {
    const container = document.querySelector('#marketplace-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    items.forEach(item => {
        const itemCard = createMarketplaceCard(item);
        container.appendChild(itemCard);
    });
}

function createMarketplaceCard(item) {
    const card = document.createElement('div');
    card.className = 'marketplace-card';
    card.innerHTML = `
        <div class="item-image">
            <img src="${item.image || '/static/images/item-placeholder.jpg'}" alt="${item.name}">
        </div>
        <div class="item-info">
            <h3>${item.name}</h3>
            <p class="item-description">${item.description}</p>
            <div class="item-details">
                <span class="price">₹${item.price}</span>
                <span class="condition">${item.condition}</span>
            </div>
            <div class="item-actions">
                <button class="btn btn-primary" onclick="buyItem(${item.id})">Buy Now</button>
                <button class="btn btn-secondary" onclick="contactSeller(${item.id})">Contact Seller</button>
            </div>
        </div>
    `;
    
    return card;
}

function buyItem(itemId) {
    if (!currentUser) {
        showLoginModal();
        return;
    }
    
    const item = marketplaceData.find(i => i.id === itemId);
    if (!item) return;
    
    showBuyModal(item);
}

function contactSeller(itemId) {
    if (!currentUser) {
        showLoginModal();
        return;
    }
    
    const item = marketplaceData.find(i => i.id === itemId);
    if (!item) return;
    
    showContactModal(item);
}

// Form handlers
function setupFormHandlers() {
    // Registration form
    const registerForm = document.querySelector('#register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegistration);
    }
    
    // Login form
    const loginForm = document.querySelector('#login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Equipment listing form
    const equipmentForm = document.querySelector('#equipment-form');
    if (equipmentForm) {
        equipmentForm.addEventListener('submit', handleEquipmentListing);
    }
    
    // Marketplace item form
    const marketplaceForm = document.querySelector('#marketplace-form');
    if (marketplaceForm) {
        marketplaceForm.addEventListener('submit', handleMarketplaceListing);
    }
}

function handleRegistration(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const userData = {
        name: formData.get('name'),
        email: formData.get('email'),
        password: formData.get('password'),
        phone: formData.get('phone'),
        location: formData.get('location')
    };
    
    fetch('/api/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Registration successful! Please login.', 'success');
            window.location.href = '/login';
        } else {
            showNotification(data.message || 'Registration failed', 'error');
        }
    })
    .catch(error => {
        console.error('Registration error:', error);
        showNotification('Registration failed. Please try again.', 'error');
    });
}

function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const loginData = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(loginData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentUser = data.user;
            sessionStorage.setItem('user', JSON.stringify(data.user));
            showNotification('Login successful!', 'success');
            window.location.href = '/dashboard';
        } else {
            showNotification(data.message || 'Login failed', 'error');
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        showNotification('Login failed. Please try again.', 'error');
    });
}

// Modal handlers
function setupModalHandlers() {
    // Close modal buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-close') || e.target.classList.contains('modal-overlay')) {
            closeModal();
        }
    });
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function showModal(modalId) {
    const modal = document.querySelector('#' + modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.style.display = 'none';
    });
    document.body.style.overflow = 'auto';
}

function showLoginModal() {
    showModal('login-modal');
}

function showRentModal(equipment) {
    const modal = document.querySelector('#rent-modal');
    if (modal) {
        modal.querySelector('#equipment-name').textContent = equipment.name;
        modal.querySelector('#equipment-price').textContent = `₹${equipment.price_per_day}/day`;
        modal.querySelector('#equipment-id').value = equipment.id;
        showModal('rent-modal');
    }
}

function showBuyModal(item) {
    const modal = document.querySelector('#buy-modal');
    if (modal) {
        modal.querySelector('#item-name').textContent = item.name;
        modal.querySelector('#item-price').textContent = `₹${item.price}`;
        modal.querySelector('#item-id').value = item.id;
        showModal('buy-modal');
    }
}

// Search functionality
function performSearch() {
    const searchInput = document.querySelector('#search-input');
    const searchTerm = searchInput.value.trim();
    
    if (!searchTerm) {
        showNotification('Please enter a search term', 'warning');
        return;
    }
    
    // Determine search context based on current page
    const currentPage = window.location.pathname;
    let searchEndpoint = '/api/search';
    
    if (currentPage.includes('equipment')) {
        searchEndpoint = '/api/equipment/search';
    } else if (currentPage.includes('marketplace')) {
        searchEndpoint = '/api/marketplace/search';
    }
    
    fetch(`${searchEndpoint}?q=${encodeURIComponent(searchTerm)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
            showNotification('Search failed. Please try again.', 'error');
        });
}

function displaySearchResults(results) {
    const container = document.querySelector('#search-results');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (results.length === 0) {
        container.innerHTML = '<p class="no-results">No results found</p>';
        return;
    }
    
    results.forEach(result => {
        const resultCard = createResultCard(result);
        container.appendChild(resultCard);
    });
}

// Filter functionality
function setupFilterHandlers() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const sortSelect = document.querySelector('#sort-select');
    const priceRange = document.querySelector('#price-range');
    
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            applyFilter(filter);
        });
    });
    
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            applySorting(this.value);
        });
    }
    
    if (priceRange) {
        priceRange.addEventListener('input', function() {
            applyPriceFilter(this.value);
        });
    }
}

function applyFilter(filter) {
    // Apply filter based on current page context
    const currentPage = window.location.pathname;
    
    if (currentPage.includes('equipment')) {
        filterEquipment(filter);
    } else if (currentPage.includes('marketplace')) {
        filterMarketplace(filter);
    }
}

function filterEquipment(category) {
    let filteredData = equipmentData;
    
    if (category !== 'all') {
        filteredData = equipmentData.filter(item => item.category === category);
    }
    
    displayEquipmentGrid(filteredData);
}

function filterMarketplace(category) {
    let filteredData = marketplaceData;
    
    if (category !== 'all') {
        filteredData = marketplaceData.filter(item => item.category === category);
    }
    
    displayMarketplaceGrid(filteredData);
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="notification-close">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
    
    // Close button handler
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
}

// Utility functions
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Image upload handler
function handleImageUpload(input, previewContainer) {
    const file = input.files[0];
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Please select a valid image file (JPEG, PNG, or GIF)', 'error');
        return;
    }
    
    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
        showNotification('Image size must be less than 5MB', 'error');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        if (previewContainer) {
            previewContainer.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px;">`;
        }
    };
    reader.readAsDataURL(file);
}

// Logout function
function logout() {
    sessionStorage.removeItem('user');
    currentUser = null;
    window.location.href = '/login';
}

// Add to favorites
function addToFavorites(itemId, type) {
    if (!currentUser) {
        showLoginModal();
        return;
    }
    
    fetch('/api/favorites', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_id: itemId,
            type: type
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Added to favorites!', 'success');
        } else {
            showNotification(data.message || 'Failed to add to favorites', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding to favorites:', error);
        showNotification('Failed to add to favorites', 'error');
    });
}

// Initialize geolocation
function initializeGeolocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                
                // Store user location for nearby searches
                sessionStorage.setItem('userLocation', JSON.stringify({lat, lon}));
                
                // Update location-based content
                loadNearbyItems(lat, lon);
            },
            function(error) {
                console.log('Location access denied or unavailable');
            }
        );
    }
}

function loadNearbyItems(lat, lon) {
    fetch(`/api/nearby?lat=${lat}&lon=${lon}`)
        .then(response => response.json())
        .then(data => {
            displayNearbyItems(data);
        })
        .catch(error => {
            console.error('Error loading nearby items:', error);
        });
}

// Initialize app on page load
window.addEventListener('load', function() {
    initializeGeolocation();
});