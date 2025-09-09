function toggleDescription(headerElement) {
    const parent = headerElement.closest('.has-description');

    // MIGHTNEED: close all other expanded items
    // document.querySelectorAll('.product-item.expanded').forEach(item => {
    //     if (item !== productItem) {
    //         item.classList.remove('expanded');
    //     }
    // });

    parent.classList.toggle('expanded');
}

