// ── TEMPLATE DASHBOARD PREVIEW ──────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll(".template-card");
    if (cards.length === 0) return; // Only execute on the templates dashboard

    const browserBody = document.querySelector(".browser-body");
    const previewTitle = document.getElementById("preview-title");
    const browserTitle = document.querySelector(".browser-url-bar span");
    const openNewTabBtn = document.getElementById("open-new-tab-btn");
    const selectedInput = document.getElementById("selected-template-input");

    const themes = [
        {
            id: 'classic-scholar',
            name: "Classic Scholar &mdash; Version 2.4.1",
            displayUrl: "preview.smartapp.io/scholar-template",
            src: "/portfolios/preview/light-1/"
        },
        {
            id: 'modern-dark',
            name: "Modern Dark &mdash; Version 1.2.0",
            displayUrl: "preview.smartapp.io/modern-dark-02",
            src: "/portfolios/preview/dark-1/"
        },
        {
            id: 'minimalist-lab',
            name: "Minimalist Lab &mdash; Version 3.1.2",
            displayUrl: "preview.smartapp.io/min-lab",
            src: "/portfolios/preview/light-2/"
        },
        {
            id: 'executive-academic',
            name: "Executive Academic &mdash; Version 1.0.5",
            displayUrl: "preview.smartapp.io/exec-academic",
            src: "/portfolios/preview/dark-2/"
        }
    ];

    function setActiveCard(card, index) {
        cards.forEach(c => {
            c.classList.remove("active");
            const badge = c.querySelector(".template-badge-primary");
            if (badge) badge.remove();
        });

        card.classList.add("active");

        const titleDiv = card.querySelector(".d-flex.align-items-center");
        if (titleDiv && !titleDiv.querySelector(".template-badge-primary")) {
            const badge = document.createElement("span");
            badge.className = "template-badge-primary ms-2";
            badge.textContent = "ACTIVE";
            titleDiv.appendChild(badge);
        }

        if (selectedInput) {
            selectedInput.value = card.dataset.template || themes[index]?.id || '';
        }

        if (previewTitle) previewTitle.innerHTML = themes[index].name;
        if (browserTitle) browserTitle.textContent = themes[index].displayUrl;
        if (openNewTabBtn) openNewTabBtn.href = themes[index].src;

        if (browserBody) {
            browserBody.style.opacity = '0';
            fetch(themes[index].src)
                .then(response => response.text())
                .then(html => {
                    setTimeout(() => {
                        browserBody.innerHTML = html;
                        browserBody.style.opacity = '1';
                    }, 150);
                })
                .catch(err => {
                    console.error('Error loading template:', err);
                    browserBody.innerHTML = '<div class="p-4 text-danger">Failed to load template preview.</div>';
                    browserBody.style.opacity = '1';
                });
        }
    }

    cards.forEach((card, index) => {
        card.addEventListener("click", () => setActiveCard(card, index));
    });

    const initialCard = document.querySelector('.template-card.active') || cards[0];
    const initialIndex = Array.from(cards).indexOf(initialCard);
    if (browserBody) {
        browserBody.style.transition = 'opacity 0.15s ease-in-out';
        if (openNewTabBtn) openNewTabBtn.href = themes[initialIndex]?.src || themes[0].src;
        setActiveCard(initialCard, initialIndex >= 0 ? initialIndex : 0);
    }
});


// ── ONBOARDING 1: WIZARD CARD SELECTION ─────────────────────────────────────
function selectCard(card) {
    document.querySelectorAll('.wizard-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');

    const btn = document.getElementById('continue-btn');
    if (btn) {
        btn.classList.remove('disabled-btn');
        btn.classList.add('enabled-btn');
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const wizardCards = document.querySelectorAll('.wizard-card');
    wizardCards.forEach(card => {
        card.addEventListener('click', function () {
            selectCard(this);
        });
    });
});


// ── ONBOARDING 2: MULTI-STEP WIZARD ─────────────────────────────────────────
const TOTAL = 6;
const sectionDone = new Array(TOTAL).fill(false);
let current = 0;

function showSection(idx) {
    document.querySelectorAll('.wizard-section').forEach((el, i) => {
        el.style.display = i === idx ? 'block' : 'none';
    });
    document.querySelectorAll('.sidebar-step').forEach((el, i) => {
        const isActive = i === idx;
        el.classList.toggle('active', isActive);
        el.classList.toggle('bg-primary', isActive);
        el.classList.toggle('text-white', isActive);
        if (isActive) {
            el.classList.remove('btn-outline-secondary');
        } else {
            el.classList.remove('bg-primary', 'text-white');
            el.classList.add('btn-outline-secondary');
        }
    });
    current = idx;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function jumpTo(idx) {
    showSection(idx);
}

function sectionValid(idx) {
    const sec = document.getElementById('section-' + idx);
    if (!sec) return true;
    let ok = true;
    sec.querySelectorAll('input[required], textarea[required], input.pub-required, textarea.pub-required, input.teach-required, textarea.teach-required').forEach(el => {
        const value = el.type === 'checkbox' || el.type === 'radio' ? el.checked : el.value.trim();
        if (!value) {
            el.classList.add('is-invalid');
            ok = false;
        } else {
            el.classList.remove('is-invalid');
        }
    });
    return ok;
}

function nextSection(idx) {
    if (!sectionValid(idx)) return;
    markDone(idx);
    if (idx + 1 < TOTAL) showSection(idx + 1);
}

function prevSection(idx) {
    if (idx > 0) showSection(idx - 1);
}

function markDone(idx) {
    sectionDone[idx] = true;
    const dot = document.getElementById('dot-' + idx);
    if (dot) {
        dot.classList.add('done');
        dot.innerHTML = '<i class="bi bi-check-lg" style="font-size:.65rem;"></i>';
    }
    updateProgress();
    checkAllDone();
}

function updateProgress() {
    const done = sectionDone.filter(Boolean).length;
    const pct = Math.round((done / TOTAL) * 100);
    const bar = document.getElementById('completion-bar');
    if (bar) {
        bar.style.width = pct + '%';
        bar.setAttribute('aria-valuenow', pct);
    }
    const pctText = document.getElementById('completion-pct');
    if (pctText) pctText.textContent = pct + '% complete';
}

function checkAllDone() {
    const btn = document.getElementById('go-step3-btn');
    if (!btn) return;
    btn.disabled = !sectionDone.every(Boolean);
}

function getSectionRequiredFields(section) {
    return section.querySelectorAll('input[required], textarea[required], select[required], input.pub-required, textarea.pub-required, input.teach-required, textarea.teach-required');
}

function updateStepButtons() {
    document.querySelectorAll('.wizard-section').forEach((section, idx) => {
        const nextButton = document.querySelector(`[data-wizard-next='${idx}']`);
        if (!nextButton) return;
        const requiredFields = getSectionRequiredFields(section);
        if (requiredFields.length === 0) {
            nextButton.disabled = false;
            return;
        }
        const valid = Array.from(requiredFields).every(el => {
            if (el.type === 'checkbox' || el.type === 'radio') {
                return el.checked;
            }
            return el.value.trim();
        });
        nextButton.disabled = !valid;
    });
}

function updateFinalContactState() {
    const scholar = document.querySelector('input[name="google_scholar"]');
    const research = document.querySelector('input[name="research_gate"]');
    const submitBtn = document.getElementById('go-step3-btn');
    const continueBtn = document.getElementById('continue-btn');
    const dot = document.getElementById('dot-5');
    const isValid = Boolean(scholar?.value.trim() || research?.value.trim());

    if (submitBtn) {
        submitBtn.disabled = !isValid;
    }

    if (dot) {
        if (isValid) {
            dot.classList.add('done');
            dot.innerHTML = '<i class="bi bi-check-lg" style="font-size:.65rem;"></i>';
            sectionDone[5] = true;
        } else {
            dot.classList.remove('done');
            dot.innerHTML = '';
            sectionDone[5] = false;
        }
    }

    if (continueBtn) {
        continueBtn.classList.toggle('disabled-btn', !isValid);
        continueBtn.classList.toggle('enabled-btn', isValid);
        continueBtn.setAttribute('aria-disabled', isValid ? 'false' : 'true');
    }

    updateProgress();
    checkAllDone();
}

function syncValidation() {
    document.querySelectorAll('input[required], textarea[required], input.pub-required, textarea.pub-required, input.teach-required, textarea.teach-required').forEach(el => {
        el.removeEventListener('input', updateStepButtons);
        el.removeEventListener('change', updateStepButtons);
        el.addEventListener('input', () => {
            if (el.value.trim()) {
                el.classList.remove('is-invalid');
            }
            updateStepButtons();
            updateFinalContactState();
        });
        el.addEventListener('change', () => {
            if (el.value.trim()) {
                el.classList.remove('is-invalid');
            }
            updateStepButtons();
            updateFinalContactState();
        });
    });

    document.querySelectorAll('input[name="google_scholar"], input[name="research_gate"]').forEach(el => {
        el.removeEventListener('input', updateFinalContactState);
        el.removeEventListener('change', updateFinalContactState);
        el.addEventListener('input', updateFinalContactState);
        el.addEventListener('change', updateFinalContactState);
    });
}


// ── ONBOARDING 2: TAG INPUT (Research Interests) ─────────────────────────────
let tags = [];

function renderTags() {
    const tagBox = document.getElementById('tag-box');
    const tagInput = document.getElementById('tag-input');
    const tagVal = document.getElementById('research-interests-val');
    if (!tagBox || !tagInput || !tagVal) return;

    tagBox.querySelectorAll('.tag-item').forEach(el => el.remove());
    tags.forEach((t, i) => {
        const span = document.createElement('span');
        span.className = 'tag-item';
        span.innerHTML = t + ' <span class="remove-tag" onclick="removeTag(' + i + ')">×</span>';
        tagBox.insertBefore(span, tagInput);
    });
    tagVal.value = tags.join(',');
    updateStepButtons();
}

function removeTag(i) {
    tags.splice(i, 1);
    renderTags();
}

document.addEventListener("DOMContentLoaded", () => {
    // Tag input listener
    const tagInput = document.getElementById('tag-input');
    if (tagInput) {
        tagInput.addEventListener('keydown', e => {
            if ((e.key === 'Enter' || e.key === ',') && tagInput.value.trim()) {
                e.preventDefault();
                tags.push(tagInput.value.trim().replace(/,$/, ''));
                tagInput.value = '';
                renderTags();
            }
        });
    }

    const tagBox = document.getElementById('tag-box');
    if (tagBox) {
        tagBox.addEventListener('click', () => {
            const tagInput = document.getElementById('tag-input');
            if (tagInput) tagInput.focus();
        });
    }

    // Photo preview listener
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const f = this.files[0];
            if (!f) return;
            const wrap = document.getElementById('photo-preview-wrap');
            if (!wrap) return;
            const reader = new FileReader();
            reader.onload = e => {
                wrap.innerHTML = '<img src="' + e.target.result + '" alt="preview" class="rounded-circle" style="width:100%; height:100%; object-fit:cover;">';
            };
            reader.readAsDataURL(f);
        });
    }

    const nextButtons = document.querySelectorAll('[data-wizard-next]');
    nextButtons.forEach(button => {
        button.addEventListener('click', () => {
            const idx = Number(button.dataset.wizardNext);
            if (!Number.isNaN(idx)) nextSection(idx);
        });
    });

    const prevButtons = document.querySelectorAll('[data-wizard-prev]');
    prevButtons.forEach(button => {
        button.addEventListener('click', () => {
            const idx = Number(button.dataset.wizardPrev);
            if (!Number.isNaN(idx)) prevSection(idx);
        });
    });

    const sidebarSteps = document.querySelectorAll('.sidebar-step');
    sidebarSteps.forEach(button => {
        button.addEventListener('click', () => {
            const idx = Number(button.dataset.step);
            if (!Number.isNaN(idx)) showSection(idx);
        });
    });

    syncValidation();

    const addPubButton = document.querySelector('[data-add-pub]');
    if (addPubButton) addPubButton.addEventListener('click', addPub);

    const addCourseButton = document.querySelector('[data-add-course]');
    if (addCourseButton) addCourseButton.addEventListener('click', addCourse);

    // Init wizard on onboarding2 page
    if (document.getElementById('step2-form')) {
        showSection(0);
        updateStepButtons();
    }
});


// ── ONBOARDING 2: ADD PUBLICATION ROW ────────────────────────────────────────
let pubCount = 1;
function addPub() {
    const c = document.getElementById('pub-container');
    if (!c) return;
    const div = document.createElement('div');
    div.className = 'pub-row';
    div.id = 'pub-' + pubCount;
    div.innerHTML = `
        <button type="button" class="remove-row-btn" onclick="this.closest('.pub-row').remove(); updateStepButtons();"><i class="bi bi-trash"></i></button>
        <div class="row g-3">
            <div class="col-md-8">
                <label class="form-label fw-semibold small">Title <span class="text-danger">*</span></label>
                <input type="text" name="pub_title[]" class="form-control pub-required" placeholder="Publication title">
            </div>
            <div class="col-md-4">
                <label class="form-label fw-semibold small">Date</label>
                <input type="date" name="pub_date[]" class="form-control">
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">PDF Link</label>
                <input type="url" name="pub_pdf[]" class="form-control" placeholder="https://...">
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">GitHub Link</label>
                <input type="url" name="pub_github[]" class="form-control" placeholder="https://github.com/...">
            </div>
        </div>`;
    c.appendChild(div);
    pubCount++;
    syncValidation();
}


// ── ONBOARDING 2: ADD COURSE ROW ─────────────────────────────────────────────
let courseCount = 1;
function addCourse() {
    const c = document.getElementById('teach-container');
    if (!c) return;
    const div = document.createElement('div');
    div.className = 'teach-row';
    div.id = 'teach-' + courseCount;
    div.innerHTML = `
        <button type="button" class="remove-row-btn" onclick="this.closest('.teach-row').remove(); updateStepButtons();"><i class="bi bi-trash"></i></button>
        <div class="row g-3">
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Course Name <span class="text-danger">*</span></label>
                <input type="text" name="course_name[]" class="form-control teach-required" placeholder="e.g. Machine Learning 101">
            </div>
            <div class="col-md-6">
                <label class="form-label fw-semibold small">Semester</label>
                <input type="text" name="teachingscol[]" class="form-control" placeholder="e.g. Fall 2024">
            </div>
            <div class="col-md-8">
                <label class="form-label fw-semibold small">Description</label>
                <textarea name="course_desc[]" class="form-control" rows="2" placeholder="Course description…"></textarea>
            </div>
            <div class="col-md-4">
                <label class="form-label fw-semibold small">Syllabus Link</label>
                <input type="url" name="syllabus_link[]" class="form-control" placeholder="https://...">
            </div>
        </div>`;
    c.appendChild(div);
    courseCount++;
    syncValidation();
}
