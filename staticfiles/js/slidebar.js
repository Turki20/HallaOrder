const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');
const links = sidebar.querySelectorAll('li');
function toggleSidebar() {
    sidebar.classList.toggle('hidden');
    localStorage.setItem('sidebarHidden',
        sidebar.classList.contains('hidden'));
}

function loadPage(page) {
    mainContent.innerHTML = `<h2>${page.charAt(0).toUpperCase() + page.slice(1)}</h2><p>Content for ${page}</p>`;

}
links.forEach(link => {
    link.addEventListener('click', () => {
        links.forEach(l => l.classList.remove('active')); link.classList.add('active'); loadPage(link.dataset.page);
    });
}); 