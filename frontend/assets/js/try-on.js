// =======================
// Global State & Constants
// =======================

// Global state
let selectedClothes = {
    tops: [],
    bottoms: [],
    user: null // changed from model
};

let currentCategory = 'tops';
let selectedItems = new Set();
let currentTryOnResult = null;
let uploadQueue = [];
let isUploading = false;

let tryOnResults = [];
let selectedResultIndex = -1;

// =======================
// Initialization
// =======================

document.addEventListener('DOMContentLoaded', () => {
    initializeUploadZones();
    updateAIComment();
    loadUserPhoto();
    loadUserClothes();
    loadTryOnResults(); // <-- Add this line
    setTimeout(() => {
        // Pre-load sample items if needed
    }, 1000);
});

// Prevent default drag behaviors on document
document.addEventListener('dragover', (e) => e.preventDefault());
document.addEventListener('drop', (e) => e.preventDefault());

// =======================
// Upload & File Handling
// =======================

function initializeUploadZones() {
    const uploadZones = document.querySelectorAll('.upload-zone');
    uploadZones.forEach(zone => {
        zone.addEventListener('click', () => {
            const fileInput = zone.querySelector('input[type="file"]') || 
                            document.getElementById(zone.id.replace('-upload', '-file')) ||
                            document.getElementById('bulk-file');
            if (fileInput) fileInput.click();
        });
    });

    // File input change handlers
    document.getElementById('tops-file').addEventListener('change', (e) => handleFileSelect(e, 'tops'));
    document.getElementById('bottoms-file').addEventListener('change', (e) => handleFileSelect(e, 'bottoms'));
    document.getElementById('user-file').addEventListener('change', (e) => handleFileSelect(e, 'user')); // changed from model-file
    document.getElementById('bulk-file').addEventListener('change', (e) => handleBulkUpload(e));
}

// Drag and drop handlers
function dragOverHandler(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function dragLeaveHandler(e) {
    e.currentTarget.classList.remove('dragover');
}

function dropHandler(e, category) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (category === 'bulk') {
        // Directly handle bulk files here
        const fileArr = Array.from(files);
        if (fileArr.length > 50) {
            alert('Maximum 50 files allowed for bulk upload');
            return;
        }
        showUploadProgress(true);
        processBulkFiles(fileArr);
    } else {
        handleFiles(files, category);
    }
}

// File handling
function handleFileSelect(e, category) {
    const files = e.target.files;
    if (category === 'user') {
        handleFiles([files[0]], category);
    } else {
        handleFiles(files, category);
    }
}

function handleBulkUpload(e) {
    const files = Array.from(e.target.files);
    if (files.length > 50) {
        alert('Maximum 50 files allowed for bulk upload');
        return;
    }
    showUploadProgress(true);
    processBulkFiles(files);
}

function processBulkFiles(files) {
    if (files.length === 0) return;
    showUploadProgress(true);

    // Use the currently selected category (tops/bottoms)
    const type = currentCategory === 'tops' ? 'Tops' : 'Bottoms';

    const formData = new FormData();
    files.forEach(file => formData.append('clothes-photos', file));
    formData.append('type', type);

    fetch('/api/user-clothes/bulk-upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(res => res.json())
    .then(results => {
        let processed = 0;
        results.forEach(res => {
            if (res && res.presigned_url && res.clothes_id) {
                addClothingItem(res.presigned_url, currentCategory, `Clothes #${res.clothes_id}`, res.clothes_id);
            }
            processed++;
            updateUploadProgress(processed, files.length);
        });
        showUploadProgress(false);
    })
    .catch(err => {
        console.error('Bulk upload failed:', err);
        showUploadProgress(false);
    });
}

function showUploadProgress(show) {
    const progress = document.getElementById('upload-progress');
    if (show) {
        progress.classList.add('active');
    } else {
        progress.classList.remove('active');
    }
}

function updateUploadProgress(current, total) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    const percentage = (current / total) * 100;
    progressFill.style.width = percentage + '%';
    progressText.textContent = `${current} of ${total} files uploaded`;
}

function handleFiles(files, category) {
    console.debug('handleFiles called', { files, category });
    Array.from(files).forEach(file => {
        if (file.type.startsWith('image/')) {
            if (category === 'user') {
                uploadUserPhotoToBackend(file).then(res => {
                    console.debug('uploadUserPhotoToBackend response', res);
                    if (res && (res.presigned_url || res.filepath)) {
                        setUserImage(res.presigned_url || `/api/s3/proxy/${res.filepath}`);
                        selectedClothes.user_id = res.photo_id;
                    } else {
                        console.error('Failed to upload user photo:', res);
                        alert('Failed to upload user photo');
                    }
                }).catch(err => {
                    console.error('Error uploading user photo:', err);
                    alert('Failed to upload user photo');
                });
            } else if (category === 'tops' || category === 'bottoms') {
                uploadUserClothesToBackend(file, category).then(res => {
                    console.debug('uploadUserClothesToBackend response', res);
                    if (res && res.presigned_url && res.clothes_id) {
                        addClothingItem(res.presigned_url, category, `Clothes #${res.clothes_id}`, res.clothes_id);
                    } else {
                        console.error('Failed to upload clothing item:', res);
                        alert('Failed to upload clothing item');
                    }
                }).catch(err => {
                    console.error('Error uploading clothing item:', err);
                    alert('Failed to upload clothing item');
                });
            } else if (category === 'bulk') {
                // No longer needed, handled in dropHandler
            } else {
                const reader = new FileReader();
                reader.onload = (e) => {
                    addClothingItem(e.target.result, category, file.name);
                };
                reader.readAsDataURL(file);
            }
        }
    });
}

async function uploadUserPhotoToBackend(file) {
    console.debug('uploadUserPhotoToBackend called', { file });
    const formData = new FormData();
    formData.append('user-photo', file);

    const response = await fetch('/api/user-photo/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });
    return response.json();
}

async function uploadUserClothesToBackend(file, category) {
    console.debug('uploadUserClothesToBackend called', { file, category });
    const formData = new FormData();
    formData.append('clothes-photo', file);
    // 'T' for tops, 'B' for bottoms
    formData.append('type', category === 'tops' ? 'Tops' : 'Bottoms');

    const response = await fetch('/api/user-clothes/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });
    return response.json();
}

function setUserImage(src) {
    console.debug('setUserImage called', { src });
    const userImage = document.getElementById('user-image');
    const placeholder = document.querySelector('.placeholder-text');
    
    userImage.src = src;
    userImage.classList.remove('hidden');
    if (placeholder) placeholder.style.display = 'none';
    
    selectedClothes.user = src;
    updateAIComment();
}

function clearUser() {
    console.debug('clearUser called');
    // Delete user photo from backend
    fetch('/api/user-photo/', {
        method: 'DELETE',
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        console.debug('User photo deleted:', data);
        const userImage = document.getElementById('user-image');
        const placeholder = document.querySelector('.placeholder-text');
        userImage.classList.add('hidden');
        selectedClothes.user = null;
        if (placeholder) placeholder.style.display = '';
        updateAIComment();
    })
    .catch(err => {
        console.error('Failed to delete user photo:', err);
        // Still clear UI even if backend fails
        const userImage = document.getElementById('user-image');
        const placeholder = document.querySelector('.placeholder-text');
        userImage.classList.add('hidden');
        selectedClothes.user = null;
        if (placeholder) placeholder.style.display = '';
        updateAIComment();
    });
}

// =======================
// Clothing Item Handling
// =======================

function addClothingItem(src, category, name, idFromBackend) {
    const item = {
        id: idFromBackend || (Date.now() + Math.random()), // Use backend id if available
        src: src,
        name: name,
        category: category
    };
    selectedClothes[category].push(item);
    renderClothingGrid(category);
    updateCategoryCounts();
    updateAIComment();
}

function removeClothingItem(id, category) {
    selectedClothes[category] = selectedClothes[category].filter(item => item.id !== id);
    selectedItems.delete(id);
    renderClothingGrid(category);
    updateCategoryCounts();
    updateAIComment();
}

function toggleItemSelection(id, category) {
    // Only allow one selection per category
    // Deselect all other items in this category
    selectedClothes[category].forEach(item => {
        selectedItems.delete(item.id);
    });
    // Select the clicked item (toggle)
    if (!selectedItems.has(id)) {
        selectedItems.add(id);
    } else {
        selectedItems.delete(id);
    }
    renderClothingGrid(category);
}

function moveItemToCategory(id, fromCategory, toCategory) {
    const itemIndex = selectedClothes[fromCategory].findIndex(item => item.id === id);
    if (itemIndex !== -1) {
        const item = selectedClothes[fromCategory].splice(itemIndex, 1)[0];
        item.category = toCategory;
        selectedClothes[toCategory].push(item);
        
        renderClothingGrid(fromCategory);
        renderClothingGrid(toCategory);
        updateCategoryCounts();
    }
}

function renderClothingGrid(category) {
    const grid = document.getElementById(`${category}-grid`);
    if (!grid) return;
    
    grid.innerHTML = '';

    selectedClothes[category].forEach(item => {
        const div = document.createElement('div');
        div.className = `clothing-item fade-in${selectedItems.has(item.id) ? ' selected' : ''}`;
        div.innerHTML = `
            <img src="${item.src}" alt="${item.name}" title="${item.name}">
        `;
        // Make the whole div clickable for selection
        div.addEventListener('click', () => toggleItemSelection(item.id, category));
        grid.appendChild(div);
    });
}

function showCategoryMenu(itemId, currentCategory) {
    const categories = ['tops', 'bottoms'];
    const options = categories
        .filter(cat => cat !== currentCategory)
        .map(cat => cat.charAt(0).toUpperCase() + cat.slice(1))
        .join('\n');
    
    const choice = prompt(`Move item to which category?\n\n${options}\n\nEnter category name:`);
    
    if (choice) {
        const targetCategory = choice.toLowerCase();
        if (categories.includes(targetCategory) && targetCategory !== currentCategory) {
            moveItemToCategory(itemId, currentCategory, targetCategory);
        }
    }
}

// =======================
// Category Management
// =======================

function switchCategory(category) {
    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-category="${category}"]`).classList.add('active');

    // Show/hide category sections
    document.querySelectorAll('.category-section').forEach(section => {
        section.classList.add('hidden');
    });
    document.getElementById(`${category}-section`).classList.remove('hidden');

    currentCategory = category;
}

function updateCategoryCounts() {
    Object.keys(selectedClothes).forEach(category => {
        if (category !== 'user') { // changed from model
            const count = selectedClothes[category].length;
            const countElement = document.getElementById(`${category}-count`);
            if (countElement) {
                countElement.textContent = count;
            }
        }
    });
}

// =======================
// AI Try-On Generation
// =======================

async function generateTryOn() {
    if (!selectedClothes.user) {
        alert('Please upload your photo first!');
        return;
    }

    // Get selected top and bottom IDs (only one per category can be selected)
    const selectedTop = selectedClothes.tops.find(item => selectedItems.has(item.id));
    const selectedBottom = selectedClothes.bottoms.find(item => selectedItems.has(item.id));

    if (!selectedTop && !selectedBottom) {
        alert('Please select at least one clothing item!');
        return;
    }

    showLoading(true);

    // Prepare payload
    const payload = {
        top_id: selectedTop ? selectedTop.id : null,
        bottom_id: selectedBottom ? selectedBottom.id : null
    };

    // Call backend to start try-on
    fetch('/api/try-on/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(result => {
        showLoading(false);
        if (result && result.image_url && result.comments) {
            showTryOnResult(result.image_url, result.comments, result.try_on_id);
        } else {
            alert(result.error || 'Try-on failed.');
        }
    })
    .catch(err => {
        showLoading(false);
        alert('Try-on failed: ' + err);
    });
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    const placeholder = document.getElementById('result-placeholder');
    
    if (show) {
        loading.classList.add('active');
        placeholder.classList.add('hidden');
    } else {
        loading.classList.remove('active');
    }
}

function showTryOnResult(src, comments, tryOnId) {
    const resultImage = document.getElementById('result-image');
    const placeholder = document.getElementById('result-placeholder');
    
    resultImage.src = src;
    resultImage.classList.remove('hidden');
    resultImage.classList.add('fade-in');
    placeholder.classList.add('hidden');
    
    currentTryOnResult = src;

    // Store both image and comments
    tryOnResults.push({ try_on_id: tryOnId, image_url: src, comments: comments });
    selectedResultIndex = tryOnResults.length - 1;
    renderTryOnGallery();

    // Show the comment for this result
    document.getElementById('ai-comment-text').textContent = comments || '';
}

// Show the selected try-on result image and comment
function showGalleryResult(idx) {
    const result = tryOnResults[idx];
    if (!result) return;
    const resultImage = document.getElementById('result-image');
    const placeholder = document.getElementById('result-placeholder');
    resultImage.src = result.image_url;
    resultImage.classList.remove('hidden');
    resultImage.classList.add('fade-in');
    placeholder.classList.add('hidden');
    currentTryOnResult = result.image_url;

    // Show the comment for this result
    document.getElementById('ai-comment-text').textContent = result.comments || '';
}

// Render the gallery thumbnails
function renderTryOnGallery() {
    const gallery = document.getElementById('tryon-gallery');
    gallery.innerHTML = '';
    tryOnResults.forEach((item, idx) => {
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.style.display = 'inline-block';

        const img = document.createElement('img');
        img.src = item.image_url;
        img.alt = `Try-On Result ${idx + 1}`;
        if (idx === selectedResultIndex) img.classList.add('selected');
        img.addEventListener('click', () => {
            selectedResultIndex = idx;
            showGalleryResult(idx);
            renderTryOnGallery();
        });

        // Add delete button
        const delBtn = document.createElement('button');
        delBtn.textContent = '✕';
        delBtn.title = 'Delete this try-on result';
        delBtn.style.position = 'absolute';
        delBtn.style.top = '2px';
        delBtn.style.right = '2px';
        delBtn.style.background = 'rgba(255,255,255,0.8)';
        delBtn.style.border = 'none';
        delBtn.style.borderRadius = '50%';
        delBtn.style.cursor = 'pointer';
        delBtn.style.width = '22px';
        delBtn.style.height = '22px';
        delBtn.style.fontSize = '16px';
        delBtn.style.lineHeight = '20px';
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteTryOnResult(idx);
        });

        wrapper.appendChild(img);
        wrapper.appendChild(delBtn);
        gallery.appendChild(wrapper);
    });
}

// =======================
// AI Comment Generation
// =======================

function updateAIComment() {
    const comments = [
        "Drag it, drop it, try it!",
        "Unleash your style with Dressique!",
        "Your next favorite look is just a click away.",
        "Mix, match, and discover your best outfit!",
        "Fashion fun starts here—give it a try!",
        "Ready to see yourself in a new style?",
        "Upload, select, and let AI do the magic!",
        "Your virtual fitting room is open!",
        "Let’s create your signature look!",
        "Try on, shine on!",
        "AI styling magic awaits you!",
        "Step into your style adventure!",
        "Express yourself—try something new today!"
    ];
    
    const randomComment = comments[Math.floor(Math.random() * comments.length)];
    document.getElementById('ai-comment-text').textContent = randomComment;
}

function generateAIComment() {
    const styleComments = [
        "Go ahead, try on a new look!",
        "Let AI inspire your next outfit.",
        "Fashion is fun—experiment with your wardrobe!",
        "See yourself in a whole new way.",
        "Your style journey starts now!"
    ];
    
    const comment = styleComments[Math.floor(Math.random() * styleComments.length)];
    document.getElementById('ai-comment-text').textContent = comment;
}

// =======================
// Utility Functions
// =======================

function resetAll() {
    // Delete user photo from backend
    fetch('/api/user-photo/', {
        method: 'DELETE',
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        console.debug('User photo deleted:', data);
        // Now clear UI state as before
        selectedClothes = { tops: [], bottoms: [], user: null };
        document.querySelectorAll('.clothes-grid').forEach(grid => grid.innerHTML = '');
        clearUser();

        const resultImage = document.getElementById('result-image');
        const placeholder = document.getElementById('result-placeholder');
        resultImage.classList.add('hidden');
        resultImage.src = '';
        placeholder.classList.remove('hidden');

        currentTryOnResult = null;
        tryOnResults = [];
        selectedResultIndex = -1;

        const gallery = document.getElementById('tryon-gallery');
        if (gallery) gallery.innerHTML = '';

        updateAIComment();
    })
    .catch(err => {
        console.error('Failed to delete user photo:', err);
        // Still reset UI even if backend fails
        selectedClothes = { tops: [], bottoms: [], user: null };
        document.querySelectorAll('.clothes-grid').forEach(grid => grid.innerHTML = '');
        clearUser();

        const resultImage = document.getElementById('result-image');
        const placeholder = document.getElementById('result-placeholder');
        resultImage.classList.add('hidden');
        resultImage.src = '';
        placeholder.classList.remove('hidden');

        currentTryOnResult = null;
        tryOnResults = [];
        selectedResultIndex = -1;

        const gallery = document.getElementById('tryon-gallery');
        if (gallery) gallery.innerHTML = '';

        updateAIComment();
    });
}

function getBrandedResultImage(callback) {
    if (!currentTryOnResult) {
        alert('No result to process. Please generate a try-on first!');
        return;
    }

    // Extract the S3 key/filename from the image URL if needed
    // Example: if currentTryOnResult is a full URL, extract the key after the bucket domain
    let s3Key = currentTryOnResult;
    if (currentTryOnResult.startsWith('http')) {
        // Example for AWS S3 URLs: https://bucket.s3.region.amazonaws.com/key
        const match = currentTryOnResult.match(/amazonaws\.com\/(.+?)(\?|$)/);
        if (match) s3Key = match[1];
    }

    fetch(`/api/s3/presigned-url?filename=${encodeURIComponent(s3Key)}`)
        .then(res => res.json())
        .then(data => {
            if (!data.url) {
                alert('Failed to get image URL.');
                return;
            }
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = function() {
                // ... your canvas drawing code here ...
                const aiComment = document.getElementById('ai-comment-text').textContent || '';
                const appName = "Dressique Virtual Try-On";
                const themeColor = "#667eea";
                const padding = 40;
                const topBar = 60;
                const bottomBar = 100;
                const width = img.width + padding * 2;
                const height = img.height + topBar + bottomBar;
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = themeColor;
                ctx.fillRect(0, 0, width, height);
                ctx.fillStyle = "#fff";
                ctx.fillRect(padding, topBar, img.width, img.height);
                ctx.font = "bold 28px Arial";
                ctx.fillStyle = "#fff";
                ctx.textAlign = "left";
                ctx.textBaseline = "top";
                ctx.fillText(appName, padding, 16);
                ctx.drawImage(img, padding, topBar, img.width, img.height);
                ctx.font = "18px Arial";
                ctx.fillStyle = "#fff";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                const commentY = height - bottomBar / 2;
                const maxWidth = width - 40;
                wrapText(ctx, aiComment, width / 2, commentY, maxWidth, 24);
                callback(canvas.toDataURL("image/png"));
            };
            img.src = data.url;
        })
        .catch(err => {
            alert('Failed to fetch image URL.');
            console.error(err);
        });

    // Helper for wrapping text
    function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
        const words = text.split(' ');
        let line = '';
        let lines = [];
        for (let n = 0; n < words.length; n++) {
            const testLine = line + words[n] + ' ';
            const metrics = ctx.measureText(testLine);
            const testWidth = metrics.width;
            if (testWidth > maxWidth && n > 0) {
                lines.push(line);
                line = words[n] + ' ';
            } else {
                line = testLine;
            }
        }
        lines.push(line);
        lines.forEach((l, i) => {
            ctx.fillText(l.trim(), x, y + i * lineHeight - ((lines.length - 1) * lineHeight) / 2);
        });
    }
}

// Download with branding
function downloadResult() {
    if (!currentTryOnResult) {
        alert('No result to download. Please generate a try-on first!');
        return;
    }
    getBrandedResultImage(function(dataUrl) {
        console.log('downloadResult: Got dataUrl', dataUrl.slice(0, 50));
        const link = document.createElement('a');
        link.download = 'virtual-tryon-result.png';
        link.href = dataUrl;
        document.body.appendChild(link); // <-- append to DOM
        link.click();
        document.body.removeChild(link); // <-- remove after click
        console.log('downloadResult: Download triggered');
    });
}

// Share with branding
function shareResult() {
    if (!currentTryOnResult) {
        alert('No result to share. Please generate a try-on first!');
        return;
    }
    getBrandedResultImage(function(dataUrl) {
        if (navigator.canShare && window.File && window.fetch) {
            fetch(dataUrl)
                .then(res => res.blob())
                .then(blob => {
                    const file = new File([blob], 'tryon-result.png', { type: blob.type });
                    if (navigator.canShare({ files: [file] })) {
                        navigator.share({
                            title: 'My Virtual Try-On Result',
                            text: 'Check out my virtual try-on result from Dressique!',
                            files: [file]
                        });
                    } else {
                        fallbackShare(dataUrl);
                    }
                })
                .catch(() => fallbackShare(dataUrl));
        } else {
            fallbackShare(dataUrl);
        }

        function fallbackShare(url) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(url);
                alert('Image link copied! Paste it to share on social media.');
            } else {
                alert('Sharing is not supported on this browser. Please save and share the image manually.');
            }
        }
    });
}

// Delete with backend
async function deleteClothingItemFromBackend(clothes_id) {
    return fetch(`/api/user-clothes/${clothes_id}`, {
        method: 'DELETE',
        credentials: 'include'
    }).then(res => res.json());
}

async function deleteSelected() {
    // Gather IDs to delete
    const idsToDelete = [];
    ['tops', 'bottoms'].forEach(category => {
        selectedClothes[category].forEach(item => {
            if (selectedItems.has(item.id)) {
                idsToDelete.push(item.id);
            }
        });
    });

    // Delete from backend
    await Promise.all(idsToDelete.map(id => deleteClothingItemFromBackend(id)));

    // Remove from frontend state
    ['tops', 'bottoms'].forEach(category => {
        selectedClothes[category] = selectedClothes[category].filter(item => !selectedItems.has(item.id));
    });
    selectedItems.clear();
    renderClothingGrid('tops');
    renderClothingGrid('bottoms');
    updateAIComment();
}

function deleteTryOnResult(idx) {
    const result = tryOnResults[idx];
    if (!result || !result.try_on_id) return;

    fetch(`/api/try-on/${result.try_on_id}`, {
        method: 'DELETE',
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        // Remove from frontend state
        tryOnResults.splice(idx, 1);
        if (selectedResultIndex >= tryOnResults.length) {
            selectedResultIndex = tryOnResults.length - 1;
        }
        if (selectedResultIndex >= 0) {
            showGalleryResult(selectedResultIndex);
        } else {
            // No results left
            const resultImage = document.getElementById('result-image');
            const placeholder = document.getElementById('result-placeholder');
            resultImage.classList.add('hidden');
            placeholder.classList.remove('hidden');
            currentTryOnResult = null;
            document.getElementById('ai-comment-text').textContent = "";
        }
        renderTryOnGallery();
    })
    .catch(err => {
        alert('Failed to delete try-on result.');
        console.error(err);
    });
}

function loadUserPhoto() {
    fetch('/api/user-photo/', { credentials: 'include' })
        .then(res => res.json())
        .then(photos => {
            if (Array.isArray(photos) && photos.length > 0 && photos[0].url) {
                setUserImage(photos[0].url);
            }
        })
        .catch(err => {
            console.error('Failed to load user photo:', err);
        });
}

function loadUserClothes() {
    fetch('/api/user-clothes/', { credentials: 'include' })
        .then(res => res.json())
        .then(clothes => {
            selectedClothes.tops = [];
            selectedClothes.bottoms = [];
            if (Array.isArray(clothes)) {
                clothes.forEach(item => {
                    const category = item.type === 'Tops' ? 'tops' : (item.type === 'Bottoms' ? 'bottoms' : null);
                    if (category) {
                        selectedClothes[category].push({
                            id: item.clothes_id,
                            src: item.presigned_url || item.url || item.filepath,
                            name: item.name || `Clothes #${item.clothes_id}`,
                            category: category
                        });
                    }
                });
            }
            renderClothingGrid('tops');
            renderClothingGrid('bottoms');
            updateCategoryCounts();
            updateAIComment();
        })
        .catch(err => {
            console.error('Failed to load user clothes:', err);
        });
}

function loadTryOnResults() {
    fetch('/api/try-on/', { credentials: 'include' })
        .then(res => res.json())
        .then(results => {
            if (Array.isArray(results) && results.length > 0) {
                tryOnResults = results.map(item => ({
                    try_on_id: item.try_on_id,
                    image_url: item.image_url || item.url,
                    comments: item.comments || ""
                }));
                selectedResultIndex = tryOnResults.length - 1;
                renderTryOnGallery();
                if (selectedResultIndex >= 0) {
                    showGalleryResult(selectedResultIndex);
                }
            }
        })
        .catch(err => {
            console.error('Failed to load try-on results:', err);
        });
}