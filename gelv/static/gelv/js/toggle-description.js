function toggleDescription(headerElement) {
    const item = headerElement.closest('.item');
    const description = item.querySelector('.description');
    
    if (description) {
        description.classList.toggle('expanded');
    }
}
