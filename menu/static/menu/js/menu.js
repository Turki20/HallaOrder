// menu/static/menu/js/menu.js

document.addEventListener('DOMContentLoaded', function() {
    // --- Main Tab Switching Logic (on main page) ---
    const tabButtons = document.querySelectorAll('.tab-btn');
    const categorySections = document.querySelectorAll('.category-section');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetId = button.dataset.target;
            tabButtons.forEach(btn => btn.classList.remove('active'));
            categorySections.forEach(section => section.classList.remove('active'));
            button.classList.add('active');
            const targetSection = document.getElementById(targetId);
            if (targetSection) { targetSection.classList.add('active'); }
        });
    });

    // --- GENERIC MODAL CONTROL LOGIC ---
    function setupModal(button, modal) {
        if (button && modal) {
            // Open modal on button click
            button.addEventListener('click', () => modal.classList.add('active'));
            
            // Close modal with the 'X' button
            const closeBtn = modal.querySelector('.close-btn');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => modal.classList.remove('active'));
            }

            // Close modal by clicking on the overlay
            modal.addEventListener('click', (e) => {
                if (e.target === modal) { modal.classList.remove('active'); }
            });

            // Handle tabs inside the modal, if they exist
            const modalTabBtns = modal.querySelectorAll('.modal-tab-btn');
            const modalTabContents = modal.querySelectorAll('.modal-tab-content');
            if (modalTabBtns.length > 0) {
                modalTabBtns.forEach(tabButton => {
                    tabButton.addEventListener('click', () => {
                        const targetId = tabButton.dataset.target;
                        modalTabBtns.forEach(btn => btn.classList.remove('active'));
                        modalTabContents.forEach(content => content.classList.remove('active'));
                        tabButton.classList.add('active');
                        const targetPanel = document.getElementById(targetId);
                        if (targetPanel) {
                            targetPanel.classList.add('active');
                        }
                    });
                });
            }
        }
    }

    // --- Initialize all modals on the page ---
    const manageCategoriesBtn = document.getElementById('manageCategoriesBtn');
    const addProductBtn = document.getElementById('addProductBtn');
    const manageOptionsBtn = document.getElementById('manageOptionsBtn');

    const manageCategoriesModal = document.getElementById('manageCategoriesModal');
    const productModal = document.getElementById('productModal');
    const manageOptionsModal = document.getElementById('manageOptionsModal');

    setupModal(manageCategoriesBtn, manageCategoriesModal);
    setupModal(addProductBtn, productModal);
    setupModal(manageOptionsBtn, manageOptionsModal);

    // --- Product Availability Toggle Logic ---
    document.body.addEventListener('change', function(e) {
        if (e.target.matches('.toggle-switch input[data-product-id]')) {
            const toggle = e.target;
            const productId = toggle.getAttribute('data-product-id');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);

            fetch(`/menu/product/${productId}/toggle/`, {
                method: 'POST', body: formData, headers: {'X-Requested-With': 'XMLHttpRequest'}
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    toggle.checked = !toggle.checked;
                    alert('حدث خطأ في تحديث حالة المنتج');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                toggle.checked = !toggle.checked;
                alert('حدث خطأ في تحديث حالة المنتج');
            });
        }
    });
});