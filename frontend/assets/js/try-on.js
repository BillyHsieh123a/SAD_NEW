// Global state
let selectedClothes = {
    tops: [],
    bottoms: [],
    model: null
};

let currentCategory = 'tops';
let selectedItems = new Set();
let currentTryOnResult = null;
let uploadQueue = [];
let isUploading = false;

let tryOnResults = []; // Store all generated results
let selectedResultIndex = -1;

// Initialize drag and drop functionality
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
    document.getElementById('model-file').addEventListener('change', (e) => handleFileSelect(e, 'model'));
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
    if (category === 'model') {
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
    uploadQueue = files.slice();
    isUploading = true;
    let processed = 0;
    
    const processNext = () => {
        if (uploadQueue.length === 0) {
            showUploadProgress(false);
            isUploading = false;
            return;
        }

        const file = uploadQueue.shift();
        const reader = new FileReader();
        
        reader.onload = (e) => {
            // Add to a temporary category
            addClothingItem(e.target.result, 'tops', file.name); // or prompt user for category
            
            processed++;
            updateUploadProgress(processed, files.length);
            
            setTimeout(processNext, 100); // Small delay to prevent blocking
        };
        
        reader.readAsDataURL(file);
    };

    processNext();
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
    Array.from(files).forEach(file => {
        if (file.type.startsWith('image/')) {
            if (category === 'model') {
                uploadModelPhotoToBackend(file).then(res => {
                    if (res && (res.presigned_url || res.filepath)) {
                        setModelImage(res.presigned_url || `/api/s3/proxy/${res.filepath}`);
                        selectedClothes.model_id = res.photo_id;
                    } else {
                        console.error('Failed to upload model photo:', res); // Debug message
                        alert('Failed to upload model photo');
                    }
                }).catch(err => {
                    console.error('Error uploading model photo:', err); // Debug message
                    alert('Failed to upload model photo');
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

// Model image handling
function setModelImage(src) {
    const modelImage = document.getElementById('model-image');
    const placeholder = document.querySelector('.placeholder-text');
    
    modelImage.src = src;
    modelImage.classList.remove('hidden');
    if (placeholder) placeholder.style.display = 'none';
    
    selectedClothes.model = src;
    updateAIComment();
}

function clearModel() {
    const modelImage = document.getElementById('model-image');
    const placeholder = document.querySelector('.placeholder-text');
    
    modelImage.classList.add('hidden');
    // if (placeholder) placeholder.style.display = 'block';
    
    selectedClothes.model = null;
    updateAIComment();
}

// Category management
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
        if (category !== 'model') {
            const count = selectedClothes[category].length;
            const countElement = document.getElementById(`${category}-count`);
            if (countElement) {
                countElement.textContent = count;
            }
        }
    });
}
// Clothing item handling
function addClothingItem(src, category, name) {
    const item = {
        id: Date.now() + Math.random(),
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

// AI Try-On Generation
function generateTryOn() {
    if (!selectedClothes.model) {
        alert('Please upload your photo first!');
        return;
    }

    if (selectedClothes.tops.length === 0 && selectedClothes.bottoms.length === 0) {
        alert('Please select at least one clothing item!');
        return;
    }

    showLoading(true);

    // Simulate AI processing
    setTimeout(() => {
        // Create composite image (simplified simulation)
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = 400;
        canvas.height = 600;

        const modelImg = new Image();
        modelImg.onload = () => {
            // Draw model
            ctx.drawImage(modelImg, 0, 0, canvas.width, canvas.height);
            
            // Add clothing overlay effect
            ctx.globalAlpha = 0.7;
            ctx.fillStyle = 'rgba(102, 126, 234, 0.2)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Convert to result
            const resultSrc = canvas.toDataURL();
            showTryOnResult(resultSrc);
            showLoading(false);
            generateAIComment();
        };
        modelImg.src = selectedClothes.model;
    }, 2000);
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

function showTryOnResult(src) {
    const resultImage = document.getElementById('result-image');
    const placeholder = document.getElementById('result-placeholder');
    
    resultImage.src = src;
    resultImage.classList.remove('hidden');
    resultImage.classList.add('fade-in');
    placeholder.classList.add('hidden');
    
    currentTryOnResult = src;

    // Always store the result, even if it's a duplicate
    tryOnResults.push(src);
    selectedResultIndex = tryOnResults.length - 1;
    renderTryOnGallery();
}

function renderTryOnGallery() {
    const gallery = document.getElementById('tryon-gallery');
    gallery.innerHTML = '';
    tryOnResults.forEach((src, idx) => {
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.style.display = 'inline-block';

        const img = document.createElement('img');
        img.src = src;
        img.alt = `Try-On Result ${idx + 1}`;
        if (idx === selectedResultIndex) img.classList.add('selected');
        img.addEventListener('click', () => {
            selectedResultIndex = idx;
            showGalleryResult(idx);
            renderTryOnGallery();
        });

        // Delete button
        const delBtn = document.createElement('button');
        delBtn.textContent = '×';
        delBtn.title = 'Delete this result';
        delBtn.style.position = 'absolute';
        delBtn.style.top = '2px';
        delBtn.style.right = '2px';
        delBtn.style.background = 'rgba(255,0,0,0.8)';
        delBtn.style.color = '#fff';
        delBtn.style.border = 'none';
        delBtn.style.borderRadius = '50%';
        delBtn.style.width = '20px';
        delBtn.style.height = '20px';
        delBtn.style.cursor = 'pointer';
        delBtn.style.fontWeight = 'bold';
        delBtn.style.zIndex = '2';
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteTryOnResult(idx);
        });

        wrapper.appendChild(img);
        wrapper.appendChild(delBtn);
        gallery.appendChild(wrapper);
    });
}

function showGalleryResult(idx) {
    const src = tryOnResults[idx];
    if (!src) return;
    const resultImage = document.getElementById('result-image');
    const placeholder = document.getElementById('result-placeholder');
    resultImage.src = src;
    resultImage.classList.remove('hidden');
    resultImage.classList.add('fade-in');
    placeholder.classList.add('hidden');
    currentTryOnResult = src;
}

// AI Comment Generation
function updateAIComment() {
    const comments = [
        "Looking great! Ready to try on some clothes?",
        "Perfect pose! Now let's see how these clothes look on you.",
        "Great selection! This combination will look amazing.",
        "Excellent choice! The colors will complement your style.",
        "Fantastic! This outfit has potential to be your new favorite."
    ];
    
    const randomComment = comments[Math.floor(Math.random() * comments.length)];
    document.getElementById('ai-comment-text').textContent = randomComment;
}

function generateAIComment() {
    const styleComments = [
        "This outfit combination creates a perfect balance between comfort and style!",
        "The colors work beautifully together - you have a great eye for fashion!",
        "This look is absolutely stunning on you. The fit is perfect!",
        "What a fantastic choice! This outfit really enhances your natural style.",
        "You're rocking this look! The proportions are spot-on.",
        "This ensemble is both trendy and timeless - a winning combination!",
        "Perfect styling! This outfit would work great for multiple occasions.",
        "The way these pieces come together is truly impressive. Great taste!"
    ];
    
    const comment = styleComments[Math.floor(Math.random() * styleComments.length)];
    document.getElementById('ai-comment-text').textContent = comment;
}

// Utility functions
function resetAll() {
    selectedClothes = { tops: [], bottoms: [], model: null };
    document.querySelectorAll('.clothes-grid').forEach(grid => grid.innerHTML = '');
    clearModel();

    const resultImage = document.getElementById('result-image');
    const placeholder = document.getElementById('result-placeholder');
    resultImage.classList.add('hidden');
    resultImage.src = ''; // <-- This line ensures the image is discarded
    placeholder.classList.remove('hidden');

    currentTryOnResult = null;
    tryOnResults = [];
    selectedResultIndex = -1;

    // Clear the try-on gallery
    const gallery = document.getElementById('tryon-gallery');
    if (gallery) gallery.innerHTML = '';

    updateAIComment();
}

function getBrandedResultImage(callback) {
    if (!currentTryOnResult) {
        alert('No result to process. Please generate a try-on first!');
        return;
    }
    const aiComment = document.getElementById('ai-comment-text').textContent || '';
    const appName = "Dressique Virtual Try-On";

    // Create a new canvas
    const img = new Image();
    img.onload = function() {
        const width = img.width;
        const height = img.height;
        const extraHeight = 100; // Space for branding and comment
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height + extraHeight;
        const ctx = canvas.getContext('2d');

        // Draw the try-on image
        ctx.drawImage(img, 0, 0, width, height);

        // Draw a white rectangle for text background
        ctx.fillStyle = "#fff";
        ctx.fillRect(0, height, width, extraHeight);

        // Draw app name
        ctx.font = "bold 24px Arial";
        ctx.fillStyle = "#667eea";
        ctx.textAlign = "center";
        ctx.fillText(appName, width / 2, height + 35);

        // Draw AI comment (wrap if too long)
        ctx.font = "16px Arial";
        ctx.fillStyle = "#333";
        const commentY = height + 65;
        const maxWidth = width - 40;
        wrapText(ctx, aiComment, width / 2, commentY, maxWidth, 22);

        // Return the new image as DataURL
        callback(canvas.toDataURL("image/png"));
    };
    img.src = currentTryOnResult;

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
            ctx.fillText(l.trim(), x, y + i * lineHeight);
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
        const link = document.createElement('a');
        link.download = 'virtual-tryon-result.png';
        link.href = dataUrl;
        link.click();
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

// Model photo upload to backend
async function uploadModelPhotoToBackend(file) {
    const formData = new FormData();
    formData.append('model-photo', file);

    const response = await fetch('/api/try-on/image/model', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });
    return response.json();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeUploadZones();
    updateAIComment();
    
    // Add some sample clothing items for demo
    setTimeout(() => {
        // You can pre-load some sample items here if needed
    }, 1000);
});

// Prevent default drag behaviors on document
document.addEventListener('dragover', (e) => e.preventDefault());
document.addEventListener('drop', (e) => e.preventDefault());

function deleteSelected() {
    // For each category, remove items whose id is in selectedItems
    ['tops', 'bottoms'].forEach(category => {
        selectedClothes[category] = selectedClothes[category].filter(item => !selectedItems.has(item.id));
    });
    // Clear selectedItems set
    selectedItems.clear();
    // Re-render grids
    renderClothingGrid('tops');
    renderClothingGrid('bottoms');
    updateAIComment();
}

function deleteTryOnResult(idx) {
    tryOnResults.splice(idx, 1);
    // Adjust selectedResultIndex if needed
    if (selectedResultIndex >= tryOnResults.length) {
        selectedResultIndex = tryOnResults.length - 1;
    }
    // Show the new selected result or hide if none left
    if (selectedResultIndex >= 0) {
        showGalleryResult(selectedResultIndex);
    } else {
        // No results left
        const resultImage = document.getElementById('result-image');
        const placeholder = document.getElementById('result-placeholder');
        resultImage.classList.add('hidden');
        placeholder.classList.remove('hidden');
        currentTryOnResult = null;
    }
    renderTryOnGallery();
}