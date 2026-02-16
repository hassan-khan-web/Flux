import './style.css'
import { parse } from './marked.js';

const form = document.getElementById('searchForm') as HTMLFormElement;
const submitBtn = document.getElementById('submitBtn') as HTMLButtonElement;
const spinner = document.getElementById('spinner') as HTMLElement;
const btnText = submitBtn.querySelector('span') as HTMLElement;

const mdOutput = document.getElementById('markdownOutput') as HTMLElement;
const jsonOutput = document.getElementById('jsonOutput') as HTMLElement;
const vectorOutput = document.getElementById('vectorOutput') as HTMLElement;

const mdPanel = mdOutput.closest('.panel') as HTMLElement;
const jsonPanel = jsonOutput.closest('.panel') as HTMLElement;
const vectorPanel = vectorOutput.closest('.panel') as HTMLElement;

const tokenStat = document.getElementById('tokenStat') as HTMLElement;
const vectorStat = document.getElementById('vectorStat') as HTMLElement;
const statusBadge = document.getElementById('statusBadge') as HTMLElement;
const queryInput = document.getElementById('queryInput') as HTMLInputElement;
const dedupStat = document.getElementById('dedupStat') as HTMLElement;
const healthDot = document.getElementById('healthDot') as HTMLElement;

const formatDropdownBtn = document.getElementById('formatDropdownBtn') as HTMLElement;
const formatDropdownMenu = document.getElementById('formatDropdownMenu') as HTMLElement;
const formatLabel = document.getElementById('selectedFormatLabel') as HTMLElement;
const formatOptions = document.getElementsByName('format_option') as NodeListOf<HTMLInputElement>;

let currentFormat = 'all';

if (formatDropdownBtn && formatDropdownMenu) {
    formatDropdownBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        formatDropdownMenu.classList.toggle('show');
    });

    document.addEventListener('click', () => {
        formatDropdownMenu.classList.remove('show');
    });

    formatDropdownMenu.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

// Option Change Logic
if (formatOptions) {
    formatOptions.forEach(opt => {
        opt.addEventListener('change', () => {
            if (opt.checked) {
                currentFormat = opt.value;
                const labelText = opt.nextElementSibling?.textContent || 'Display All';
                if (formatLabel) formatLabel.textContent = labelText;

                updatePanelVisibility(currentFormat);

                if (formatDropdownMenu) formatDropdownMenu.classList.remove('show');
            }
        });
    });
}

function updatePanelVisibility(format: string) {
    if (!mdPanel || !jsonPanel || !vectorPanel) return;

    if (format === 'all') {
        mdPanel.classList.remove('hidden');
        jsonPanel.classList.remove('hidden');
        vectorPanel.classList.remove('hidden');
        return;
    }

    mdPanel.classList.add('hidden');
    jsonPanel.classList.add('hidden');
    vectorPanel.classList.add('hidden');

    if (format === 'markdown') mdPanel.classList.remove('hidden');
    if (format === 'json') jsonPanel.classList.remove('hidden');
    if (format === 'vector') vectorPanel.classList.remove('hidden');
}


// Prevent default form submission and run search
if (form) {
    form.addEventListener('submit', async (e: Event) => {
        e.preventDefault();
        performSearch();
    });
}

async function performSearch(): Promise<void> {
    const query = queryInput.value.trim();
    const region = (document.getElementById('region') as HTMLSelectElement).value;
    const language = (document.getElementById('language') as HTMLSelectElement).value;
    const limitInput = document.getElementById('limit') as HTMLInputElement;
    let limit = limitInput ? parseInt(limitInput.value) : 10;
    if (limit > 50) limit = 50;

    // UI Loading State
    submitBtn.disabled = true;
    spinner.style.display = 'block';
    btnText.textContent = 'Processing...';

    const apiFormat = currentFormat === 'all' ? 'vector' : currentFormat;

    if (!query) {
        mdOutput.textContent = "Please enter a query or URL.";
        jsonOutput.textContent = "{}";
        statusBadge.textContent = 'Input Required';
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        btnText.textContent = 'Run Extraction';
        return;
    }

    // Animation Logic
    let loadingInterval: any;
    const startLoadingAnimation = (elements: HTMLElement[]) => {
        let dots = '';
        loadingInterval = setInterval(() => {
            dots = dots.length < 3 ? dots + '.' : '';
            elements.forEach(el => el.textContent = `Fetching data${dots}`);
        }, 500);
    };

    const activeStatElements: HTMLElement[] = [];
    if (!mdPanel.classList.contains('hidden')) activeStatElements.push(mdOutput);
    if (!jsonPanel.classList.contains('hidden')) jsonOutput.textContent = 'Fetching data...';
    if (!jsonPanel.classList.contains('hidden')) activeStatElements.push(jsonOutput);
    if (!vectorPanel.classList.contains('hidden')) activeStatElements.push(vectorOutput);

    if (activeStatElements.length > 0) {
        activeStatElements.forEach(el => el.textContent = 'Fetching data');
        startLoadingAnimation(activeStatElements);
    }

    tokenStat.textContent = '...';
    statusBadge.textContent = 'Loading...';

    const isUrl = /^(http|https):\/\/[^ "]+$/.test(query);
    const mode = isUrl ? 'scrape' : 'search';

    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                mode: mode,
                region: region,
                language: language,
                limit: limit,
                output_format: apiFormat
            })
        });

        if (!response.ok) {
            throw new Error(`Start failed: ${response.statusText}`);
        }

        const initData = await response.json();
        const taskId = initData.task_id;
        let data: any = null;

        // Polling Loop
        while (true) {
            await new Promise(resolve => setTimeout(resolve, 2000)); // 2s wait

            const pollRes = await fetch(`/tasks/${taskId}`);
            if (!pollRes.ok) throw new Error("Polling failed");

            const pollData = await pollRes.json();

            if (pollData.status === 'completed') {
                data = pollData.result;
                if (!data) throw new Error("Task completed but no data returned.");
                break;
            } else if (pollData.status === 'failed') {
                throw new Error(pollData.error || "Task failed on server");
            }
        }

        // Update UI
        const mdContent = data.formatted_output || "No output generated.";
        try {
            mdOutput.innerHTML = parse(mdContent) as string;
        } catch (e) {
            console.error("Markdown parse error:", e);
            mdOutput.textContent = mdContent;
        }

        const jsonData = JSON.parse(JSON.stringify(data));
        if (jsonData.organic_results) {
            jsonData.organic_results.forEach((r: any) => delete r.embedding);
        }
        jsonOutput.textContent = JSON.stringify(jsonData, null, 2);

        if (data.organic_results && data.organic_results.length > 0) {
            const vectors = data.organic_results.filter((r: any) => r.embedding);
            if (vectors.length > 0) {
                vectorStat.textContent = `${vectors.length} Vecs`;
                const sample = vectors.map((r: any, i: number) =>
                    `[Result ${i + 1}] Dims: ${r.embedding.length}\n[${r.embedding.join(', ')}]`
                ).join('\n\n');
                vectorOutput.textContent = sample;
            } else {
                vectorStat.textContent = "0 Vecs";
                vectorOutput.textContent = "No vectors returned.";
            }
        } else {
            vectorOutput.textContent = "No results.";
        }

        if (data.token_estimate) {
            tokenStat.textContent = `~${data.token_estimate} Tokens`;
        }

        // Scoring Logic (Global Sync)
        const relBadges = document.querySelectorAll('.relevance-score');
        const credBadges = document.querySelectorAll('.credibility-score');

        if (data.relevance_score !== undefined) {
            const score = data.relevance_score;
            relBadges.forEach(badge => {
                const el = badge as HTMLElement;
                el.textContent = `Rel: ${Math.round(score * 100)}%`;
                el.title = data.relevance_reasoning || "Relevance Score";
                el.className = 'badge score-badge relevance-score ' + (score > 0.7 ? 'score-high' : score > 0.4 ? 'score-med' : 'score-low');
            });
        }

        if (data.credibility_score !== undefined) {
            const score = data.credibility_score;
            credBadges.forEach(badge => {
                const el = badge as HTMLElement;
                el.textContent = `Cred: ${Math.round(score * 100)}%`;
                el.title = data.credibility_reasoning || "Source Credibility";
                el.className = 'badge score-badge credibility-score ' + (score > 0.7 ? 'score-high' : score > 0.4 ? 'score-med' : 'score-low');
            });
        }

        statusBadge.textContent = response.ok ? (data.cached ? 'Cached ⚡' : 'Live 🟢') : 'Error 🔴';

        // Road to 9/10: New UI Indicators
        if (dedupStat) {
            if (data.deduplicated_count > 0) {
                dedupStat.textContent = `${data.deduplicated_count} Filtered`;
                dedupStat.classList.remove('hidden');
            } else {
                dedupStat.classList.add('hidden');
            }
        }

        if (healthDot && data.provider_health) {
            let totalSuccess = 0;
            let totalFailure = 0;
            Object.values(data.provider_health).forEach((h: any) => {
                totalSuccess += h.success || 0;
                totalFailure += h.failure || 0;
            });

            const total = totalSuccess + totalFailure;
            const rate = total > 0 ? totalSuccess / total : 1.0;

            healthDot.className = 'health-dot';
            if (rate > 0.9) healthDot.classList.add('health-good');
            else if (rate > 0.5) healthDot.classList.add('health-warning');
            else healthDot.classList.add('health-critical');

            healthDot.title = `Scraper Health: ${Math.round(rate * 100)}% (${totalSuccess}/${total})`;
        }

    } catch (err: any) {
        mdOutput.textContent = "Error connecting to API.";
        jsonOutput.textContent = err?.toString() || 'Unknown Error';
        statusBadge.textContent = 'Connection Fail';
    } finally {
        if (loadingInterval) clearInterval(loadingInterval);
        submitBtn.disabled = false;
        spinner.style.display = 'none';
        btnText.textContent = 'Run Extraction';
    }
}
