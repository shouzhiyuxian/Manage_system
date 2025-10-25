// static/script.js
let searchTimer;

document.getElementById('positionSearch').addEventListener('input', function(e) {
    const keyword = e.target.value.trim();
    clearTimeout(searchTimer);

    if (keyword.length === 0) {
        document.getElementById('searchResults').style.display = 'none';
        return;
    }

    searchTimer = setTimeout(() => {
        fetch(`/search?q=${encodeURIComponent(keyword)}`)
            .then(response => response.json())
            .then(data => {
                const resultsContainer = document.getElementById('searchResults');
                resultsContainer.innerHTML = '';

                if (data.length > 0) {
                    data.forEach(position => {
                        const div = document.createElement('div');
                        div.className = 'search-item';
                        div.textContent = position;
                        div.onclick = () => {
                            document.getElementById('positionSearch').value = position;
                            resultsContainer.style.display = 'none';
                            // 这里可以添加选中后的处理逻辑
                        };
                        resultsContainer.appendChild(div);
                    });
                    resultsContainer.style.display = 'block';
                } else {
                    resultsContainer.style.display = 'none';
                }
            });
    }, 300); // 300ms防抖
});
