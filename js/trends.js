const loadingSpinner = document.getElementById('loading-spinner');
const trendContent = document.getElementById('trend-content');
const listGainers = document.getElementById('list-gainers');
const listLosers = document.getElementById('list-losers');

async function fetchTrends() {
    try {
        const res = await fetch('http://localhost:5000/streaks');
        const data = await res.json();

        renderList(listGainers, data.gainers, 'Up');
        renderList(listLosers, data.losers, 'Down');

        loadingSpinner.style.display = 'none';
        trendContent.style.display = 'grid';

    } catch (error) {
        console.error(error);
        loadingSpinner.innerHTML = `<span style="color:red">${i18n.t('scan_connect_fail')}</span>`;
    }
}

function renderList(container, items, direction) {
    container.innerHTML = '';

    if (items.length === 0) {
        container.innerHTML = `<li style="padding:1rem; text-align:center; color:var(--text-secondary)">${i18n.t('trend_no_data')}</li>`;
        return;
    }

    items.forEach(item => {
        const li = document.createElement('li');

        const changeColor = direction === 'Up' ? 'var(--success-color)' : 'var(--danger-color)';
        const streakBg = direction === 'Up' ? 'var(--success-bg)' : 'var(--danger-bg)';
        const sign = direction === 'Up' ? '+' : '';

        li.style.cursor = 'pointer';

        li.innerHTML = `
            <div style="display:flex; flex-direction:column;">
                <span style="font-family:var(--font-data); font-size:1.2rem; font-weight:700; color:var(--text-primary);">${item.symbol}</span>
                <span style="font-size:0.9rem; color:${changeColor}; font-weight:500;">
                    ${sign}${item.total_change.toFixed(2)}%
                </span>
            </div>
            
            <div style="text-align:right;">
                <div style="background:${streakBg}; color:${changeColor}; padding:0.25rem 0.75rem; border-radius:50px; font-weight:700; font-family:var(--font-data); display:inline-block;">
                    ${item.streak} ${i18n.t('lbl_days')}
                </div>
                <div style="font-size:0.8rem; margin-top:0.3rem; color:var(--text-secondary);">Last: ${item.price.toFixed(2)}</div>
            </div>
        `;

        li.addEventListener('click', () => {
            localStorage.setItem('targetStock', item.symbol);
            window.location.href = 'index.html';
        });

        container.appendChild(li);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    fetchTrends();
});

window.addEventListener('langChange', () => {
    fetchTrends();
});
