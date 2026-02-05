function article(link) {
    // implicitly cited by `render_node`
    const iframe = document.getElementById('article');
    iframe.setAttribute('src', link);
}

const node_collapsed_triangle = `
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus" viewBox="0 0 16 16">
  <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4"></path>
</svg>
`;

const node_expanded_triangle = `
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-dash" viewBox="0 0 16 16">
  <path d="M4 8a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7A.5.5 0 0 1 4 8"></path>
</svg>
`;

function switch_sub(button) {
    const expanded = button.innerHTML === node_expanded_triangle;
    const current_level = parseInt(button.parentNode.getAttribute('level'));
    let chapter = button.parentNode.nextElementSibling;
    while (chapter) {
        const level = parseInt(chapter.getAttribute('level'));
        if (isNaN(level) || level <= current_level) {
            break;
        }
        if (expanded) {
            chapter.classList.remove('d-flex');
            chapter.style.display = "none";
            const chapter_button = chapter.querySelector('a[role="button"]');
            if (chapter_button) {
                chapter_button.innerHTML = node_collapsed_triangle;
            }
        } else {
            if (level > current_level + 1) {
                chapter = chapter.nextElementSibling;
                continue;
            }
            chapter.classList.add('d-flex');
            chapter.style.display = "flex";
        }
        chapter = chapter.nextElementSibling;
    }
    if (expanded) {
        button.innerHTML = node_collapsed_triangle;
    } else {
        button.innerHTML = node_expanded_triangle;
    }
}

function render_node(item) {
    return `
        <li class="nav-item mb-2 d-flex justify-content-between" level="${item['level']}" 
            style="line-height: calc(var(--bs-body-line-height)); ${item['show'] ? '' : 'display: none !important;'} ">
            <a ${item['filepath'] ? `href="javascript:article('${item['filepath']}')"` : ''} 
                style="padding: 0.23rem ${item['level']}rem;">
                ${item['name']}
            </a> 
            ${item['has_sub'] ? `<a role="button" class="me-4" onclick="switch_sub(this)" style="padding: 0.23rem;">
                ${node_collapsed_triangle}</a>` : ''}
        </li>
    `;
}

function get_book_identifier() {
    return window.location.pathname.replace(/index\.html$/, '');
}

function generate_node(nodes, level) {
    let toc_item = [];
    let show = (level === 0);
    const path = get_book_identifier();
    const iframe_src = localStorage.getItem(`${path}bookmark_src`);
    for (let node of nodes) {
        toc_item.push({'name': node['name'], 'level': level, 'filepath': node['filepath'],
            'show': show, 'has_sub': Boolean(node['sub'])});
        if (iframe_src && node['filepath'] === iframe_src) {
            show = true;
        }
        if (node['sub']) {
            const data = generate_node(node['sub'], level + 1);
            show = show || data['show'];
            toc_item.push(...data['toc_item']);
        }
    }
    if (show) {
        for (let m of toc_item) {
            if (m['level'] === level) m['show'] = true;
        }
    }
    return {'show': show, 'toc_item': toc_item};
}

function initialize_toc_bookmark(articles_list) {
    let articles_html = '';
    let toc_items = generate_node(articles_list, 0);
    for (let item of toc_items['toc_item']) {
        articles_html += render_node(item);
    }
    const iframe = document.getElementById('article');
    const path = get_book_identifier();
    const saved_y = localStorage.getItem(`${path}bookmark_y`);
    const saved_src = localStorage.getItem(`${path}bookmark_src`);
    iframe.onload = () => {
        if (saved_y) {
            iframe.contentWindow.scrollTo(0, parseInt(saved_y));
        }
        function set_bookmark() {
            localStorage.setItem(`${path}bookmark_src`, iframe.contentWindow.location.href);
            localStorage.setItem(`${path}bookmark_y`, iframe.contentWindow.scrollY.toString());
        }
        iframe.contentWindow.addEventListener("scroll", set_bookmark);
        set_bookmark();
    };
    if (saved_src) {
        fetch(saved_src, { method: 'HEAD' }) // Check if the URL exists
            .then(response => {
                if (response.ok) article(saved_src)
            })
            .catch(() => {
                // Do nothing if URL is not accessible (404 or other errors)
            });
    }
    return articles_html;
}
