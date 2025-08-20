// static/yourapp/admin/js/issue_admin.js
document.addEventListener('DOMContentLoaded', function() {
    var journalField = document.getElementById('id_journal');
    var numberField = document.getElementById('id_number');
    
    if (journalField && numberField) {
        journalField.addEventListener('change', function() {
            var journalId = this.value;
            if (journalId) {

                var currentPath = window.location.pathname;
                console.log('Current path:', currentPath);

                fetch('/admin/gelv/issue/get-next-issue-number/?journal_id=' + journalId)
                    .then(response => response.text())
                    .then(data => {
                        console.log(data)
                        numberField.value = data;
                    });
            } else {
                numberField.value = '';
            }
        });
    }
});
