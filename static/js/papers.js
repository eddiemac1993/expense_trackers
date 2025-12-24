document.addEventListener('DOMContentLoaded', function () {
    const addRowBtn = document.getElementById('add-row');
    const tableBody = document.querySelector('#items-table tbody');
    const totalForms = document.getElementById('id_items-TOTAL_FORMS');

    addRowBtn.addEventListener('click', function () {
        const rowCount = tableBody.children.length;
        const newRow = tableBody.children[0].cloneNode(true);

        newRow.querySelectorAll('input').forEach(input => {
            input.value = '';
            const name = input.name.replace(/\d+/, rowCount);
            const id = input.id.replace(/\d+/, rowCount);
            input.name = name;
            input.id = id;
        });

        tableBody.appendChild(newRow);
        totalForms.value = rowCount + 1;
    });

    tableBody.addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-row')) {
            e.target.closest('tr').remove();
        }
    });
});
