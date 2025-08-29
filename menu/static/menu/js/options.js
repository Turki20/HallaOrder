// menu/static/menu/js/options.js

document.addEventListener('DOMContentLoaded', function () {
    // --- Toggle visibility of multi-select rules ---
    const selectionTypeSelect = document.querySelector('#id_selection_type');
    const multiSelectRulesDiv = document.querySelector('#multi-select-rules');

    if (selectionTypeSelect && multiSelectRulesDiv) {
        selectionTypeSelect.addEventListener('change', function () {
            if (this.value === 'MULTIPLE') {
                multiSelectRulesDiv.classList.remove('d-none');
            } else {
                multiSelectRulesDiv.classList.add('d-none');
            }
        });
    }

    // --- Dynamic Formset Logic ---
    const container = document.getElementById('options-form-container');
    const addButton = document.getElementById('add-form-row');
    const emptyFormTemplate = document.getElementById('empty-form-template')?.innerHTML;
    const totalFormsInput = document.querySelector('#id_options-TOTAL_FORMS');

    if (!container || !addButton || !emptyFormTemplate || !totalFormsInput) {
        return; // Exit if essential elements are not on the page
    }

    // Add new form
    addButton.addEventListener('click', function () {
        let formNum = parseInt(totalFormsInput.value);
        const newFormHtml = emptyFormTemplate.replace(/__prefix__/g, formNum);
        
        container.insertAdjacentHTML('beforeend', newFormHtml);
        totalFormsInput.value = formNum + 1;

        updatePositions();
    });

    // Remove form
    container.addEventListener('click', function (e) {
        const removeButton = e.target.closest('.remove-form-row');
        if (removeButton) {
            const row = removeButton.closest('.option-form-row');
            const deleteInput = row.querySelector('input[type="checkbox"][id$="-DELETE"]');
            
            if (deleteInput) {
                deleteInput.checked = true;
                row.style.display = 'none';
            } else {
                row.remove();
                totalFormsInput.value = parseInt(totalFormsInput.value) - 1;
                updateFormIndices(); 
            }
            updatePositions();
        }
    });

    // Helper to update hidden position fields
    function updatePositions() {
        const rows = container.querySelectorAll('.option-form-row');
        rows.forEach((row, index) => {
            const positionInput = row.querySelector('input[id$="-position"]');
            if (positionInput) {
                positionInput.value = index;
            }
        });
    }

    // Helper to re-index forms after a new one is removed
    function updateFormIndices() {
        const rows = container.querySelectorAll('.option-form-row');
        const totalForms = rows.length;
        totalFormsInput.value = totalForms;

        for (let i = 0; i < totalForms; i++) {
            const row = rows[i];
            const inputs = row.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                const name = input.getAttribute('name');
                const id = input.getAttribute('id');
                if (name) {
                    input.setAttribute('name', name.replace(/options-\d+-/, `options-${i}-`));
                }
                if (id) {
                    input.setAttribute('id', id.replace(/id_options-\d+-/, `id_options-${i}-`));
                }
            });
        }
    }
});