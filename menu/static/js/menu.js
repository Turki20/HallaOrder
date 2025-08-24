document.addEventListener('DOMContentLoaded', function() {
    // --- Tab Switching Logic ---
    const tabButtons = document.querySelectorAll('.tab-btn');
    const categorySections = document.querySelectorAll('.category-section');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetId = button.dataset.target;
            tabButtons.forEach(btn => btn.classList.remove('active'));
            categorySections.forEach(section => section.classList.remove('active'));
            button.classList.add('active');
            document.getElementById(targetId)?.classList.add('active');
        });
    });
    // --- Modal Control Logic ---
    const manageCategoriesBtn = document.getElementById('manageCategoriesBtn');
    const addProductBtn = document.getElementById('addProductBtn');
    const manageCategoriesModal = document.getElementById('manageCategoriesModal');
    const productModal = document.getElementById('productModal');
    if (manageCategoriesBtn) manageCategoriesBtn.addEventListener('click', () => manageCategoriesModal.classList.add('active'));
    if (addProductBtn) addProductBtn.addEventListener('click', () => productModal.classList.add('active'));
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        const closeBtn = modal.querySelector('.close-btn');
        if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.remove('active'));
        modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('active'); });
    });
});