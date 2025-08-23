function toggleDescription(headerElement) {
    const productItem = headerElement.closest('.product-item');

    // MIGHTNEED: close all other expanded items
    // document.querySelectorAll('.product-item.expanded').forEach(item => {
    //     if (item !== productItem) {
    //         item.classList.remove('expanded');
    //     }
    // });

    productItem.classList.toggle('expanded');
}

