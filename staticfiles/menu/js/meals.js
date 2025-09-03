// menu/static/menu/js/meals.js
document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('meal-items-container');
    const addButton = document.getElementById('add-item-row');
    const emptyFormTemplate = document.getElementById('empty-item-template')?.innerHTML;
    const totalFormsInput = document.querySelector('#id_items-TOTAL_FORMS');
    if (!container || !addButton || !emptyFormTemplate || !totalFormsInput) return;
    
    addButton.addEventListener('click', function () {
        let formNum = parseInt(totalFormsInput.value);
        const newFormHtml = emptyFormTemplate.replace(/__prefix__/g, formNum);
        container.insertAdjacentHTML('beforeend', newFormHtml);
        totalFormsInput.value = formNum + 1;
    });

    container.addEventListener('click', function (e) {
        const removeButton = e.target.closest('.remove-item-row');
        if (removeButton) {
            const row = removeButton.closest('.meal-item-row');
            const deleteInput = row.querySelector('input[type="checkbox"][id$="-DELETE"]');
            if (deleteInput) {
                deleteInput.checked = true;
                row.style.display = 'none';
            } else {
                row.remove();
                totalFormsInput.value = parseInt(totalFormsInput.value) - 1;
                updateFormIndices();
            }
        }
    });

    function updateFormIndices() {
        const rows = container.querySelectorAll('.meal-item-row');
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const inputs = row.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                const name = input.getAttribute('name');
                const id = input.getAttribute('id');
                if (name) input.setAttribute('name', name.replace(/items-\d+-/, `items-${i}-`));
                if (id) input.setAttribute('id', id.replace(/id_items-\d+-/, `id_items-${i}-`));
            });
        }
    }
});