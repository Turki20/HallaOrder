document.addEventListener('DOMContentLoaded', function() {
    // --- Tab Switching Logic ---
    const tabButtons = document.querySelectorAll('.tab-btn');
    const categorySections = document.querySelectorAll('.category-section');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetId = button.dataset.target;
            
            // Remove active class from all tabs and sections
            tabButtons.forEach(btn => btn.classList.remove('active'));
            categorySections.forEach(section => section.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding section
            button.classList.add('active');
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.classList.add('active');
            }
        });
    });

    // --- Modal Control Logic ---
    const manageCategoriesBtn = document.getElementById('manageCategoriesBtn');
    const addProductBtn = document.getElementById('addProductBtn');
    const manageCategoriesModal = document.getElementById('manageCategoriesModal');
    const productModal = document.getElementById('productModal');

    // Open modals
    if (manageCategoriesBtn && manageCategoriesModal) {
        manageCategoriesBtn.addEventListener('click', () => {
            manageCategoriesModal.classList.add('active');
        });
    }
    
    if (addProductBtn && productModal) {
        addProductBtn.addEventListener('click', () => {
            productModal.classList.add('active');
        });
    }

    // Close modals
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        const closeBtn = modal.querySelector('.close-btn');
        
        // Close on X button click
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        }
        
        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    // --- Product Availability Toggle Logic (FIXED) ---
    const toggleSwitches = document.querySelectorAll('.toggle-switch input[data-product-id]');
    
    toggleSwitches.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const productId = this.getAttribute('data-product-id');
            
            if (productId) {
                // Get CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                // Create form data
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', csrfToken);
                
                // Send AJAX request
                fetch(`/menu/product/${productId}/toggle/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        // If failed, revert the toggle
                        this.checked = !this.checked;
                        alert('حدث خطأ في تحديث حالة المنتج');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    // If failed, revert the toggle
                    this.checked = !this.checked;
                    alert('حدث خطأ في تحديث حالة المنتج');
                });
            }
        });
    });

    // --- Form Validation ---
    const addProductForm = document.querySelector('#productModal form');
    if (addProductForm) {
        addProductForm.addEventListener('submit', function(e) {
            const name = this.querySelector('[name="name"]').value.trim();
            const price = this.querySelector('[name="price"]').value;
            const category = this.querySelector('[name="category"]').value;
            
            if (!name || !price || !category) {
                e.preventDefault();
                alert('يرجى ملء جميع الحقول المطلوبة');
                return false;
            }
            
            if (parseFloat(price) <= 0) {
                e.preventDefault();
                alert('يرجى إدخال سعر صحيح');
                return false;
            }
        });
    }

    const addCategoryForm = document.querySelector('#manageCategoriesModal form');
    if (addCategoryForm) {
        addCategoryForm.addEventListener('submit', function(e) {
            const name = this.querySelector('[name="name"]').value.trim();
            
            if (!name) {
                e.preventDefault();
                alert('يرجى إدخال اسم الفئة');
                return false;
            }
        });
    }
});