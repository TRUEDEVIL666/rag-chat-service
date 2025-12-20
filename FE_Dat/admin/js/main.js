// admin/js/main.js

document.addEventListener("DOMContentLoaded", function() {
    // 1. Tìm cái thẻ div chờ sẵn để nhét sidebar vào
    const sidebarContainer = document.getElementById("sidebar-container");
    
    if (sidebarContainer) {
        // 2. Tải file sidebar.html về
        fetch('components/sidebar.html')
            .then(response => response.text())
            .then(data => {
                // 3. Nhét code HTML vào
                sidebarContainer.innerHTML = data;
                
                // 4. Logic tô màu menu đang chọn (Active State)
                highlightActiveMenu();
            })
            .catch(error => console.error('Lỗi tải sidebar:', error));
    }
});

function highlightActiveMenu() {
    // Lấy tên file hiện tại trên URL (ví dụ: documents.html)
    const path = window.location.pathname;
    const page = path.split("/").pop() || 'index.html'; // Mặc định là index.html nếu rỗng

    // Tìm thẻ <a> có data-page trùng với tên file
    const activeLink = document.querySelector(`a[data-page="${page}"]`);
    
    if (activeLink) {
        // Xóa class cũ (màu xám)
        activeLink.classList.remove('text-gray-600', 'hover:bg-blue-50');
        // Thêm class mới (màu xanh active)
        activeLink.classList.add('bg-blue-50', 'text-blue-600', 'font-medium');
        
        // Đổi icon từ rỗng sang đặc (fill) cho đẹp nếu thích
        const icon = activeLink.querySelector('i');
        if(icon) {
            icon.classList.remove('ph');
            icon.classList.add('ph-fill');
        }
    }
}