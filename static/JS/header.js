
document.addEventListener('DOMContentLoaded', function() {
    let csrfToken = "{{ csrf_token() }}";

    function rotate(gearElement) {
        let angle = 0;
        setInterval(() => {
            angle = (angle + 5) % 360; 
            gearElement.style.transform = `rotate(${angle}deg)`;
        }, 50); 
    
    }

    function myLoader(color) {
        if (color === undefined) {
          color = 'crimson'
        }
        let loader = document.createElement('div'); // Create a div element for the loader
          loader.id = 'gear';
          loader.style.color = color;
          loader.style.fontSize = '20px';
          loader.style.display = 'inline-block';
          loader.textContent = '⚙';
          return loader;
    }
      
    // function addToCartXML(newCookies) {

    //     let formData = new FormData();
    //     formData.append('newCookies', newCookies);

    //     // Create a new XMLHttpRequest object
    //     let xhr = new XMLHttpRequest();
        
    //     // Configure the request
    //     xhr.open('POST', '/add-to-cart');
        

    //     xhr.setRequestHeader('X-CSRFToken', csrfToken);

    //     // Define what happens on successful data submission
    //     xhr.onload = function () {
    //         if (xhr.status === 200) {
    //             let response = JSON.parse(xhr.responseText);

    //             // let mistakesDiv = document.getElementById('mistakes_modal');
    //             // mistakesDiv.innerHTML = ''; // Clear previous messages
                
    //             if (response.status === '0') {
    //                 // Handle Unknown Error
    //                 // mistakesDiv.textContent = response.answer;
    //                 // mistakesDiv.style.color = 'red';

    //                 // Scroll the window to the mistakesDiv with smooth behavior
    //                 // mistakesDiv.scrollIntoView({ behavior: 'smooth' });

    //                 saveButton.classList.remove('hidden');
    //                 saving.classList.add('hidden');

    //             } 
                
    //             if (response.status === '1') {
    //                 // Handle success
    //                 // alert(response.answer);
    //                 let currentUrl = window.location.href;
    //                 location.href = currentUrl;
    //             }

    //         } else {
    //             // Handle error response
    //             saveButton.classList.remove('hidden');
    //             saving.classList.add('hidden');

    //             console.error('Error adding category:', xhr.responseText);
    //         }
    //     };

    //     // Send the request with the FormData object
    //     xhr.send(formData);

    //                 // });
    // }


    function basket() {
        let Cart = cookie.get('Cart', false);
        let notification = document.querySelector('.notification');
        if (Cart === false) {
            notification.innerHtml = '';
            notification.style.display = 'none';
        } else {
            arr = Cart.split('&')
            let cartCount = arr.length;
            notification.textContent = cartCount;
            notification.style.display = 'block';
        }

    }

    // Add to card
    function addToCart(ptID, num) {
        let Cart = cookie.get('Cart');
        let flagID = false;
        let flagNum = false;
        let newPt = false;
        let newCookie = '';
        if (Cart) {
            arr = Cart.split('&');
            arr.forEach(item => {
                array = item.split('-');
                if (array[0] === ptID) {
                    flagID = true; 
                    if (array[1] === num) {
                        flagNum = true; 
                        return;
                    } else {
                        let newItem = ptID + '-' + num;
                        newCookie = newCookie + '&' + newItem;
                    }  

                } else { 
                    newPt = true;
                    newCookie = newCookie + '&' + item;
                }
                
            });
            newCookie = newCookie.substring(1);
            
        } else {
            newCookie = ptID + '-' + num;   
        }
        
        if (flagNum === true) {
            alert('You have already added this product,\nYou can change the quantoty\nBut change this alert to a nice modal window')
            return;
        } else {

            if (newPt === true && flagID === false) {
                newCookie = Cart + '&' + ptID + '-' + num;  
            }
            // let serverResponse = addToCartXML(newCookie);
            // console.log(`serverResponse is ${serverResponse}`)
            // if (serverResponse) {
            //     cookie.set('Cart', newCookie, { expires: 7 })  
            // } else {
                //     alert('Something is wrong. But this alert is temporarly!')
                // }
                
            cookie.set('Cart', newCookie, { expires: 7 })  
            basket();
        }

    }


    let cartState = false
    const addToCartBtns = document.getElementsByClassName('add-to-cart-btn');
    const quantity = document.getElementsByClassName('quantity');
    for (let i = 0; i < addToCartBtns.length; i++) {
        addToCartBtns[i].onclick = function() {
            console.log(`cartState before is ${cartState}`)
            if (cartState) {
                return;
            }
            cartState = true;
            console.log(`cartState after is ${cartState}`)
            
            let clickedBotton = addToCartBtns[i];

            let loader = myLoader();    
    
            clickedBotton.appendChild(loader);
        
            let gearElement = document.getElementById('gear');
            if (!gearElement) {
              return;
            } 
        
            rotate(gearElement);
            // clickedBotton.textContent = '{{ _("Adding ") }}';
            let ptID = clickedBotton.value;
            let num = quantity[i].value;
            addToCart(ptID, num)  
            // setTimeout(() => (gearElement.remove(), 3050)); 
            setTimeout(() => {
                gearElement.remove();
            }, 3000);
            
            cartState = false;
        };
    }
    
    // Buy now
    let buyNowBtns = document.getElementsByClassName('buy-btn');
    for (let i = 0; i < buyNowBtns.length; i++) {
        buyNowBtns[i].onclick = function() {
            alert('Buy Now clicked!');
        };
    }

    basket();

});

