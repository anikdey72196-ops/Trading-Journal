document.addEventListener('DOMContentLoaded', () => {
    
    // Disable "Add Trade" button if daily limit is reached
    const btn = document.getElementById('addTradeBtn');
    
    if (btn) {
        const remaining = parseInt(btn.dataset.remaining, 10);
        
        if (remaining <= 0) {
            // Apply disabled styling
            btn.style.backgroundColor = '#27272A';
            btn.style.color = '#A1A1AA';
            btn.style.cursor = 'not-allowed';
            btn.title = 'Daily trade limit reached';
            
            // Prevent navigation
            btn.addEventListener('click', e => e.preventDefault());
        }
    }

    // Automatically refresh the page at exactly midnight
    // so the user is thrown to the target-setting form if they leave the tab open
    function scheduleMidnightRefresh() {
        const now = new Date();
        const nextMidnight = new Date(
            now.getFullYear(),
            now.getMonth(),
            now.getDate() + 1, // Next day
            0, 0, 0 // exactly 12:00 AM (midnight)
        );
        const msUntilMidnight = nextMidnight.getTime() - now.getTime();
        
        setTimeout(() => {
            window.location.reload();
        }, msUntilMidnight);
    }

    scheduleMidnightRefresh();
});