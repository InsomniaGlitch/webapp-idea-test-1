document.addEventListener("DOMContentLoaded", function () {
    const orderInput = document.querySelector("input[name='order']");
    const sortOptions = document.querySelectorAll(".sort-option");
    const filterPanel = document.querySelector('.filter-panel');
    const activeSort = filterPanel ? filterPanel.dataset.activeSort : null;
    const activeOrder = filterPanel ? filterPanel.dataset.activeOrder : null;

    // initialize order and checked radio from server-provided data
    if (activeOrder) {
        orderInput.value = activeOrder;
    }
    if (activeSort) {
        const radio = document.querySelector(`input[name="sort_by"][value="${activeSort}"]`);
        if (radio) radio.checked = true;
    }

    function refreshArrows() {
        const checked = document.querySelector('input[name="sort_by"]:checked');
        const field = checked ? checked.value : null;
        sortOptions.forEach((opt) => {
            const arrow = opt.querySelector(".sort-arrow");
            const radio = opt.querySelector("input[type='radio']");
            const f = radio ? radio.value : null;
            if (!arrow) return;
            arrow.dataset.field = f || "";
            arrow.textContent = f === field ? (orderInput.value === "asc" ? "↑" : "↓") : "";
        });
    }

    const filterForm = document.querySelector('.filter-panel form');
    sortOptions.forEach((opt) => {
        opt.addEventListener("click", function (event) {
            const radio = opt.querySelector("input[type='radio']");
            if (!radio) return;
            const field = radio.value;

            const checked = document.querySelector('input[name="sort_by"]:checked');
            const currentField = checked ? checked.value : null;
            if (currentField === field) {
                orderInput.value = orderInput.value === "asc" ? "desc" : "asc";
            } else {
                orderInput.value = "asc";
            }

            radio.checked = true;
            radio.dispatchEvent(new Event("change", { bubbles: true }));
            refreshArrows();
            if (filterForm) {
                filterForm.submit();
            }
        });
    });

    if (filterForm) {
        const autoSubmitInputs = filterForm.querySelectorAll("input[type='checkbox'], input[type='number'], input[type='date'], input[type='text']");
        autoSubmitInputs.forEach((input) => {
            input.addEventListener('change', () => filterForm.submit());
        });
    }

    document.querySelectorAll(".audio-player").forEach((player) => {
        const audio = player.querySelector("audio");
        const playButton = player.querySelector(".play-toggle");
        const progress = player.querySelector(".progress-bar");
        const currentTimeEl = player.querySelector(".current-time");
        const durationEl = player.querySelector(".duration-time");
        const volume = player.querySelector(".volume-slider");
        const speedBtn = player.querySelector('.speed-btn');
        const speedOverlay = player.querySelector('.speed-overlay');

        if (!audio) return;

        // ensure play button shows initial play symbol
        if (playButton) playButton.textContent = "▶";
        if (audio.dataset && audio.dataset.src) {
            audio.src = audio.dataset.src;
            audio.load();
        }

        player.querySelectorAll("[data-action]").forEach((button) => {
            button.addEventListener("click", function (event) {
                event.preventDefault();
                const action = button.dataset.action;
                if (action === "toggle") {
                    if (audio.paused) {
                        audio.play();
                        playButton.textContent = "❚❚";
                    } else {
                        audio.pause();
                        playButton.textContent = "▶";
                    }
                } else if (action === "seek-back") {
                    audio.currentTime = Math.max(0, audio.currentTime - 10);
                } else if (action === "seek-forward") {
                    audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 10);
                } else if (action === "start") {
                    audio.currentTime = 0;
                } else if (action === "end") {
                    audio.currentTime = audio.duration || 0;
                }
            });
        });

        audio.addEventListener("play", () => {
            // pause any other playing audio
            document.querySelectorAll('audio').forEach((a) => {
                if (a !== audio) a.pause();
            });
            if (playButton) playButton.textContent = "❚❚";
        });
        audio.addEventListener("pause", () => {
            if (playButton) playButton.textContent = "▶";
        });

        audio.addEventListener("loadedmetadata", () => {
            durationEl.textContent = formatTime(audio.duration || 0);
            progress.max = audio.duration || 100;
        });

        audio.addEventListener("timeupdate", () => {
            currentTimeEl.textContent = formatTime(audio.currentTime);
            if (audio.duration) {
                progress.value = audio.currentTime;
            }
        });

        progress.addEventListener("input", () => {
            audio.currentTime = Number(progress.value);
        });

        if (volume) {
            volume.addEventListener("input", () => {
                audio.volume = Number(volume.value);
            });
        }

        const isPreview = player.dataset.preview === "true";
        const previewLimit = 60;

        if (speedBtn && speedOverlay) {
            speedBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                speedOverlay.classList.toggle('open');
            });

            speedOverlay.querySelectorAll('.speed-option').forEach(opt => {
                opt.addEventListener('click', (e) => {
                    const val = Number(opt.dataset.speed);
                    audio.playbackRate = val;
                    speedBtn.textContent = opt.textContent;
                    speedOverlay.classList.remove('open');
                });
            });

            document.addEventListener('click', (e) => {
                if (!speedOverlay.contains(e.target) && e.target !== speedBtn) {
                    speedOverlay.classList.remove('open');
                }
            });
        }

        if (isPreview) {
            const enforcePreview = () => {
                if (audio.currentTime >= previewLimit) {
                    audio.pause();
                    audio.currentTime = previewLimit;
                    if (playButton) {
                        playButton.textContent = "▶";
                    }
                    audio.removeEventListener('timeupdate', enforcePreview);
                }
            };
            audio.addEventListener('timeupdate', enforcePreview);
        }

        audio.addEventListener("contextmenu", (event) => event.preventDefault());
    });

    refreshArrows();

    const cartToggle = document.querySelector('.cart-toggle-button');
    const cartPanel = document.querySelector('.cart-panel');
    const cartClose = document.querySelector('.cart-close-button');

    if (cartToggle && cartPanel) {
        cartToggle.addEventListener('click', () => cartPanel.classList.toggle('open'));
    }
    if (cartClose && cartPanel) {
        cartClose.addEventListener('click', () => cartPanel.classList.remove('open'));
    }
    document.addEventListener('click', (e) => {
        if (cartPanel && !cartPanel.contains(e.target) && e.target !== cartToggle) {
            cartPanel.classList.remove('open');
        }
    });
});

function formatTime(seconds) {
    if (!Number.isFinite(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
    return `${mins}:${secs}`;
}
