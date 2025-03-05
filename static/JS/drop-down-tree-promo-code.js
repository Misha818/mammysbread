document.addEventListener('DOMContentLoaded', () => {
  
    const selectedLabel = document.getElementById('selected-label');
    const parentOptions = document.getElementById('parent-options');
    const parentItems = document.querySelectorAll('#parent-options .option');
    const parentTitles = document.querySelectorAll('.parent-title');
    

    // Keep track of the last clicked child to revert its style if needed
    let lastSelectedChild = null;
    if (document.getElementsByClassName('.selected-child')) {
        let lastSelectedChild = document.querySelector('.selected-child');
    } 



    // 1) Toggle the list of parent items when the top label is clicked
    selectedLabel.addEventListener('click', (e) => {
      parentOptions.classList.toggle('hidden');
    });

    // 2) For each parent, populate or toggle children on click
    parentTitles.forEach((parentTitle) => {

      parentTitle.addEventListener('click', (e) => {
        // Prevent the click from closing the parent list
        e.stopPropagation();
        
        // Hide children of ALL other parents first
        parentTitles.forEach((otherTitle) => {
          if (otherTitle !== parentTitle) {
            const otherChildContainer = otherTitle.parentNode.parentNode.querySelector('.child-options');
            otherChildContainer.classList.add('hidden');
          }

        });


          // if (e.target !== parentItem) {
          //   console.log(e.target.className); 
          //   return;
          // }


          // Get the child container for this parent
        const childContainer = parentTitle.parentNode.parentNode.querySelector('.child-options');

        // If it's already populated, just toggle it
        if (childContainer.innerHTML.trim() !== '') {
          childContainer.classList.toggle('hidden');
          return;
        }

        // Otherwise, create child items from data-children
        const children = parentTitle.parentNode.parentNode.getAttribute('data-children').split('_sppr_');
        children.forEach((childInfo) => {
          
          let childArr = childInfo.split('_sp_');
          let childValue = childArr[0];
          let childName = childArr[1];

          const childDiv = document.createElement('div');
          
          const childCheckbox = document.createElement('input');
              childCheckbox.type = 'checkbox';
              childCheckbox.className = 'child-checkbox';

          if (childValue === 'null') {
              childName = 'Click on me to add a product type'
              childDiv.className = 'child-option';
              childDiv.textContent = childName;
              childDiv.dataset.value = childValue.trim();
              ptA = document.createElement('a');
              ptA.href = window.origin + '/add-price/' + parentItem.getAttribute('data-value')
              ptA.appendChild(childDiv)
              childContainer.appendChild(ptA);
              
          } else {
              childDiv.className = 'child-option';
              childDiv.dataset.value = childValue.trim();
              
              childCheckbox.id = 'child_checkbox_' + childValue.trim();
              const childDivName = document.createElement('span');
              childDivName.textContent = childName.trim();
              
              const discountValue = document.createElement('input');



              const discountGroupDiv = document.createElement('div');
              discountGroupDiv.className = "input-group flex-nowrap";
              // Set inline styles
              discountGroupDiv.style.width = "auto";
              discountGroupDiv.style.gap = "0";
              discountGroupDiv.style.margin = "0 0 0 auto";

              // Create the input element
              const input = document.createElement('input');
              input.type = "text";
              input.classList = "form-control child-discount";
              input.setAttribute('aria-label', "Username");
              input.setAttribute('aria-describedby', "addon-wrapping");
              input.setAttribute('title', "Add Discount Rate");
              // Set inline styles for input
              input.style.padding = "3px";
              input.style.width = "33px";
              input.style.height = "33px";

              input.addEventListener('input', function() {
                    
                  // Check if input is numeric
                  if (!/^\d*\.?\d+$/.test(this.value) && this.value !== '') {
                      input.value = this.value.slice(0, -1); 
                      return;
                  }
                  let valFloat = 0;
                  if (this.value !== '') {
                    valFloat = parseFloat(this.value);
                  }


                  const grandpa = this.parentNode.parentNode;
                  const bigDeddy = this.parentNode.parentNode.parentNode.parentNode;

                  const revardInput = grandpa.querySelector('.revard-input').value;
                  const childCheckbox = grandpa.querySelector('.child-checkbox');

                  console.log(`revardInput is ${revardInput.length}`);
                  console.log(`valFloat is ${valFloat}`);



                  if (revardInput.length === 0 && valFloat < 1) {
                     childCheckbox.checked = false; 
                  } else {
                    childCheckbox.checked = true; 
                  }

                  if (valFloat > 99 || valFloat < 1) {
                      input.value = this.value.slice(0, -1);                       
                      return;
                  }


                  const parentDiscountInput = bigDeddy.querySelector('.parent-discount');
                  const parentCheckbox = bigDeddy.querySelector('.parent-checkbox');
                  parentDiscountInput.value = '';  
                  parentCheckbox.checked = false;                   

              });

              // Create the span element
              const span = document.createElement('span');
              span.className = "input-group-text";
              span.id = "addon-wrapping";
              // Set inline styles for span
              span.style.height = "33px";
              span.style.width = "25px";
              span.style.padding = "5px";
              // Set the text content of the span
              span.textContent = "%";

              // Append the input and span to the outer div
              discountGroupDiv.appendChild(input);
              discountGroupDiv.appendChild(span);


              const revardDiv = document.createElement('div');
              revardDiv.className = "input-group flex-nowrap";
              // Set inline styles
              revardDiv.style.width = "auto";
              revardDiv.style.gap = "0px";
              revardDiv.style.margin = "0px 0px 0px 5px";
              revardDiv.style.flexDirection = "row";
              revardDiv.style.alignItems = "center";

              // Create the input element
              const inputElement = document.createElement('input');
              inputElement.type = "text";
              inputElement.classList = "form-control revard-input";
              inputElement.setAttribute('aria-label', 'Username');
              inputElement.setAttribute('aria-describedby', 'addon-wrapping');
              inputElement.title = "Revard Value";
              // Set inline styles for the input
              inputElement.style.padding = "3px";
              inputElement.style.width = "33px";
              inputElement.style.height = "33px";

              // Create the select element
              const selectElement = document.createElement('select');
              selectElement.className = "form-select form-select-revard";
              selectElement.id = "inputGroupSelect03";
              selectElement.setAttribute('aria-label', 'Example select with button addon');
              selectElement.title = "Revard Options";
              // Set inline styles for the select
              selectElement.style.height = "33px";
              selectElement.style.padding = "0px 30px 0px 11px";
              selectElement.style.width = "60px";

              // Create the first option (selected by default)
              const option1 = document.createElement('option');
              option1.selected = true;
              option1.value = "0";
              option1.textContent = "%";

              // Create the second option
              const option2 = document.createElement('option');
              option2.value = "1";
              option2.textContent = "fx";

              // Append the options to the select element
              selectElement.appendChild(option1);
              selectElement.appendChild(option2);

              // Append the input and select elements to the container div
              revardDiv.appendChild(inputElement);
              revardDiv.appendChild(selectElement);

              childDiv.appendChild(childCheckbox);
              childDiv.appendChild(childDivName);
              childDiv.appendChild(discountGroupDiv);
              childDiv.appendChild(revardDiv);

              
              childContainer.appendChild(childDiv);
              
          } 
          
        });

        // Show the newly populated child container
        childContainer.classList.remove('hidden');
      });

    });
    
      // (Optional) If user clicks anywhere outside the dropdown, close it
      // document.addEventListener('click', (e) => {
      //   // If the click is not inside the dropdown or its children, hide it
      //   const isClickInside = e.target.closest('.dropdown');
      //   if (!isClickInside) {
      //     parentOptions.classList.add('hidden');
      //   }
      // });

      
    });
    


  