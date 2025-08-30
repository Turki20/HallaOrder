// menu/static/menu/js/gallery.js

document.addEventListener('DOMContentLoaded', function () {
    const galleryGrid = document.getElementById('gallery-grid');
    const imageUploadInput = document.getElementById('image-upload-input');
    const previewContainer = document.getElementById('image-preview-container');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    if (!galleryGrid) return;

    // --- Event Delegation for Gallery Actions ---
    galleryGrid.addEventListener('click', function (e) {
        const setCoverBtn = e.target.closest('.set-cover-btn');
        const deleteBtn = e.target.closest('.delete-image-btn');

        if (setCoverBtn) {
            const galleryItem = setCoverBtn.closest('.gallery-item');
            const imageId = galleryItem.dataset.imageId;
            handleSetCover(imageId, galleryItem);
        }

        if (deleteBtn) {
            const galleryItem = deleteBtn.closest('.gallery-item');
            const imageId = galleryItem.dataset.imageId;
            if (confirm('هل أنت متأكد من حذف هذه الصورة؟')) {
                handleDeleteImage(imageId, galleryItem);
            }
        }
    });

    // --- AJAX Handlers ---
    function handleSetCover(imageId, galleryItem) {
        fetch(`/menu/product/image/${imageId}/set-cover/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove existing cover badge and "Set Cover" button
                const currentCover = galleryGrid.querySelector('.cover-badge');
                if (currentCover) {
                    const oldCoverItem = currentCover.closest('.gallery-item');
                    oldCoverItem.querySelector('.set-cover-btn')?.classList.remove('d-none');
                    currentCover.remove();
                }

                // Add new cover badge and hide the "Set Cover" button
                galleryItem.insertAdjacentHTML('beforeend', '<div class="cover-badge"><i class="fas fa-star"></i> غلاف</div>');
                galleryItem.querySelector('.set-cover-btn').classList.add('d-none');
                
                // Re-order element to be first
                galleryGrid.prepend(galleryItem);
            } else {
                alert('فشل تعيين الصورة كغلاف.');
            }
        })
        .catch(error => console.error('Error setting cover:', error));
    }

    function handleDeleteImage(imageId, galleryItem) {
        fetch(`/menu/product/image/${imageId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                galleryItem.remove();
            } else {
                alert('فشل حذف الصورة.');
            }
        })
        .catch(error => console.error('Error deleting image:', error));
    }

    // --- New Image Upload Preview ---
    if (imageUploadInput && previewContainer) {
        imageUploadInput.addEventListener('change', function(event) {
            previewContainer.innerHTML = ''; // Clear previous previews
            const files = event.target.files;

            for (const file of files) {
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const previewItem = `
                            <div class="gallery-item preview-item">
                                <img src="${e.target.result}" alt="Preview">
                                <div class="gallery-item-overlay">
                                    <span class="preview-text">سيتم الرفع عند الحفظ</span>
                                </div>
                            </div>
                        `;
                        previewContainer.insertAdjacentHTML('beforeend', previewItem);
                    }
                    reader.readAsDataURL(file);
                }
            }
        });
    }
});