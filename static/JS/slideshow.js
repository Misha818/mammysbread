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


if (images.length < 5) {
    document.querySelector('.thumbnails-wrapper').style.width = '100%';
}
let returnChecker = false;
let scrollPosition = 0;
let scrollCounter = 1
let maxShownThumbnails = 5;
let scrollNumber = Math.floor(images.length / maxShownThumbnails) +  (images.length % maxShownThumbnails === 0 ? 0 : 1);

let thumbnailImage = document.querySelector('.thumbnails img');
let imgHeight = thumbnailImage ? thumbnailImage.offsetHeight : 0;
let imgStyle = window.getComputedStyle(thumbnailImage);
let marginBottom = imgStyle.marginBottom;
marginBottom = parseInt(marginBottom.replace("px", ""), 10);

let itemHeight = imgHeight + marginBottom;
let scrollTo = 0;
// let thumbnailsWrapperHeight = itemHeight * maxShownThumbnails;
let thumbnailsWrapperHeight = document.querySelector('.thumbnails-wrapper').offsetHeight;

// function displaySize() {
//     const width = window.innerWidth;
//     const height = window.innerHeight;
//     thumbnailsWrapperHeight = document.querySelector('.thumbnails-wrapper').offsetHeight;
//     console.log(`Current thumbnailsWrapperHeight: ${thumbnailsWrapperHeight}px`);
//   }

//   // Initial size display
// //   displaySize();

//   // Event listener for resize events
//   window.addEventListener('resize', displaySize);




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
        scrollPosition = num;
    } else {
        console.log('Image not found');
    }

}

function nextImage() {
    if (typeof currentImageIndex === "string") {
        currentImageIndex = Number(currentImageIndex);
    }

    if (currentImageIndex === images.length - 1) {
        currentImageIndex = 0;
    } else {
        currentImageIndex = currentImageIndex + 1;
        currentImageIndex = Math.min(currentImageIndex, images.length - 1);
    }

    showImage(currentImageIndex);
    scrollThumbnails('right', true);
}

function prevImage() {
    // currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
    if (typeof currentImageIndex === "string") {
        currentImageIndex = Number(currentImageIndex);
    }

    if (currentImageIndex === 0) {
        currentImageIndex = images.length - 1;
    } else {
        currentImageIndex = currentImageIndex - 1;
        // currentImageIndex = Math.min(currentImageIndex, images.length - 1);
    }
    showImage(currentImageIndex);
    scrollThumbnails('left', true);
}


// let nextScroll = maxShownThumbnails;

const maxScroll = images.length - maxShownThumbnails; // Adjust if you display more or fewer thumbnails
const thumbnailContainer = document.querySelector('.thumbnails');


function scrollThumbnails(direction, stop) {
    
    // Scroll to the left
    if (direction === 'left') {

        if (stop === true) { // Sliders
            console.log(`scrollPosition ${scrollPosition}`)
            let x = 0;
            if (scrollPosition === images.length - 1) {
                x = 1;
            }
            let scrollChecker = Math.ceil((scrollPosition + x) / maxShownThumbnails);
            if (scrollChecker !== scrollCounter) {
                if (scrollChecker === scrollNumber) { // shows last group of images
                    scrollCounter = scrollChecker;
                    if (images.length % maxShownThumbnails > 0) { // if num of last image group is less then maxShownThumbnails
                        scrollTo = thumbnailsWrapperHeight * (scrollCounter - 2) + itemHeight * (images.length % maxShownThumbnails) + marginBottom * (scrollCounter - 1);
                    } else {
                        scrollTo = thumbnailsWrapperHeight * (scrollCounter - 1);
                    }
                } else {
                    if (scrollChecker * maxShownThumbnails === scrollPosition + 1) {
                        scrollCounter = scrollChecker;
                        scrollTo = thumbnailsWrapperHeight * (scrollCounter - 1);
                    }
                }
            }

        }
        
    
        if (stop === false) { // Thumbnails

            scrollCounter = scrollCounter - 1;
            if (scrollCounter === 0) {
                scrollCounter = scrollNumber;
            } 
            if (scrollCounter === scrollNumber) {

                if (images.length % maxShownThumbnails > 0) { // if num of last image group is less then maxShownThumbnails
                    scrollTo = thumbnailsWrapperHeight * (scrollCounter - 2) + itemHeight * (images.length % maxShownThumbnails) + marginBottom * (scrollCounter - 1);
                } else {
                    scrollTo = thumbnailsWrapperHeight * (scrollCounter - 1);
                }
            } else {
                scrollTo = thumbnailsWrapperHeight * (scrollCounter - 1);
            }

        }


    } else {
        // Scroll to Right
        if (stop === true) { // Sliders

            let scrollChecker = Math.floor(scrollPosition / maxShownThumbnails) + 1;
            if (scrollChecker !== scrollCounter) {
                if (scrollChecker === scrollNumber) { // shows last group of images
                    if (images.length % maxShownThumbnails > 0) { // if num of last image group is less then maxShownThumbnails
                        scrollTo = thumbnailsWrapperHeight * (scrollCounter - 1) + itemHeight * (images.length % maxShownThumbnails) + marginBottom * (scrollCounter - 1);
                    } else {
                        scrollTo = thumbnailsWrapperHeight * scrollCounter;
                    }
                    scrollCounter = scrollChecker;
                } else {
                    if (scrollChecker * maxShownThumbnails === scrollPosition + 1) {
                        scrollCounter = scrollChecker;
                        scrollTo = thumbnailsWrapperHeight * (scrollCounter - 1);
                    }
                    scrollCounter = scrollChecker;
                    scrollTo = thumbnailsWrapperHeight * (scrollCounter - 1);
                }
            }

        }

        if (stop === false) { // Thumbnails
            
            if (scrollCounter === scrollNumber) {
                scrollCounter = 1;
                scrollTo = 0;       
                
            } else if (scrollCounter === scrollNumber - 1) { 
                if (images.length % maxShownThumbnails > 0) { // if num of last image group is less then maxShownThumbnails
                    
                    scrollTo = thumbnailsWrapperHeight * (scrollCounter - 1) + itemHeight * (images.length % maxShownThumbnails) + marginBottom * (scrollCounter - 1);
                    scrollCounter = scrollCounter + 1;
                } else {
                    scrollTo = thumbnailsWrapperHeight * scrollCounter;
                    scrollCounter = scrollCounter + 1;
                }
            } else {
                scrollTo = thumbnailsWrapperHeight * scrollCounter;
                scrollCounter = scrollCounter + 1;
            }
            
        }    
    }
    
    thumbnailContainer.style.transform = `translateY(-${scrollTo}px)`; // Adjust based on thumbnail size and gap
}

function changeType(typeID) {
    let spss = document.querySelectorAll('.productType');
    if (spss) {
        spss.forEach(function(span) {
            span.style.display = 'none';
        });
        document.getElementById('type_' + typeID).style.display = 'block';
    }
}
