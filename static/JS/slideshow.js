
let currentImageIndex = 0;
const thumbnails = document.querySelectorAll('.thumbnails img');
const images = [];
const imagesSRC = [];

thumbnails.forEach(thumbnail => {
    const src = thumbnail.getAttribute('src');
    const imageName = src.split('/').pop();
    imagesSRC.push(src);
    images.push(imageName);
});

let scrollPosition = 0;
let maxShownThumbnails = 5;


function showImage(num) {
    currentImageIndex = num;
    // section = Math.ceil((currentImageIndex + 1) / maxShownThumbnails)
    const imageSrc = imagesSRC[num]; // Ռեալում սա պետք չի գա
    const image = document.getElementById('main-image');
    const thumbnails = document.querySelectorAll('.thumbnails img');
    thumbnails.forEach(thumbnail => thumbnail.classList.remove('selectedThumbnail'));
    image.classList.remove('fade');  // Reset animation
    void image.offsetWidth;  // Trigger reflow to restart the animation
    image.src = imageSrc;  // Update the source
    image.classList.add('fade');  // Add the fade class for transition
    
    const img = document.querySelector(`.thumbnails img[src="${imageSrc}"]`);
    if (img) {
        img.classList.add('selectedThumbnail')
        scrollPosition = num - 1;
    } else {
        console.log('Image not found');
    }

}

function nextImage() {
    currentImageIndex = (currentImageIndex + 1) % images.length;
    showImage(currentImageIndex);
    scrollThumbnails('right', true);
}

function prevImage() {
    currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
    showImage(currentImageIndex);
    scrollThumbnails('left', true);
}


// let nextScroll = maxShownThumbnails;

const maxScroll = images.length - maxShownThumbnails; // Adjust if you display more or fewer thumbnails
const thumbnailContainer = document.querySelector('.thumbnails');


function scrollThumbnails(direction, stop) {
    
    let img  = document.querySelector('.thumbnails img');
    let imgWidth = parseInt(img.width, 10);
    let imgStyle = window.getComputedStyle(img);
    let marginRight = imgStyle.marginRight;
    let scrollTo = 0;
    marginRight = parseInt(marginRight.replace("px", ""), 10);
    
    if (direction === 'left') {
        if (scrollPosition === images.length - 2) { 
            scrollPosition = images.length - maxShownThumbnails;
        } else {
            scrollPosition = Math.min(scrollPosition - 1, maxScroll);
            if (scrollPosition < 0) {
                scrollPosition = 0;
            }
        }

        scrollTo = (scrollPosition * (imgWidth + marginRight)) - (scrollPosition * (imgWidth + marginRight)) % 10
        
    } else {
        scrollPosition = Math.min(scrollPosition + 1, maxScroll);
        scrollTo = (scrollPosition * (imgWidth + marginRight)) - (scrollPosition * (imgWidth + marginRight)) % 10
    }
    
    thumbnailContainer.style.transform = `translateX(-${scrollTo}px)`; // Adjust based on thumbnail size and gap
}

