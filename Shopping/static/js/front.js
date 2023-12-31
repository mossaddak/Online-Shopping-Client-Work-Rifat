$(function () {


    /* ===============================================================
         LIGHTBOX
      =============================================================== */
    lightbox.option({
        'resizeDuration': 200,
        'wrapAround': true
    });


    /* ===============================================================
         PRODUCT SLIDER
      =============================================================== */
    $('.product-slider').owlCarousel({
        items: 1,
        thumbs: true,
        thumbImage: false,
        thumbsPrerendered: true,
        thumbContainerClass: 'owl-thumbs',
        thumbItemClass: 'owl-thumb-item'
    });


    /* ===============================================================
         PRODUCT QUNATITY
      =============================================================== */

    function cartPricing(response) {

        // Retrive the price from response
        var overall_product_price_of_cart = response.overall_product_price_of_cart

        // Get class
        var total_item_price_class = '.total_item_price' + response.id

        // Set total item price 
        $(total_item_price_class).text("Tk" + response.total_price);

        // Set overall cart item price
        $(".subtotal").text("Tk" + overall_product_price_of_cart);

        // Set shipping charge with overall cart item price
        $(".total_price_with_shipping").text("Tk" + (parseFloat(overall_product_price_of_cart) + 10.00).toFixed(2));

    }

    // Decreament the cart item qty from database
    function minusCart(cartId) {
        $.ajax({
            url: '/minus-cart/' + cartId + '/',
            type: 'GET',
            success: function (response) {
                if (response.status === "success") {
                    cartPricing(response);
                } else {
                    console.error("Error decrementing product quantity:", response);
                }
            }
        });
    }

    // Increament the cart item qty from database
    function plusCart(cartId) {
        $.ajax({
            url: '/plus-cart/' + cartId + '/',
            type: 'GET',
            success: function (response) {
                if (response.status === "success") {
                    cartPricing(response)
                } else {
                    console.error("Error decrementing product quantity:", response);
                }
            }
        });
    }

    // Decreament
    $(document).on('click', '.dec-btn', function (e) {
        e.preventDefault();

        var siblings = $(this).siblings('input');

        if (parseInt(siblings.val(), 10) === 1) {
            // Show the confirmation dialog
            var confirmation = confirm('Are you sure you want to delete this item?');
            if (confirmation) {
                // Hide the current "minus" button
                $(this).hide();

                // Replace with the new button HTML
                var newButton = '<a class="dec-btn p-0 ml-2" onclick="return confirm(\'Are you sure you want to delete this item?\')" href="{% url \'store:minus-cart\' cart_product.id %}"><i class="fas fa-minus"></i></a>';
                $(this).after(newButton);

                // Get cart id
                var cartId = $(this).data('cart-id');

                // Get cart_product class
                var cart_product_class = ".cart_product" + cartId

                // Delete the cart item
                $(cart_product_class).hide("slow", function () {
                    $(this).remove();
                });

                // Minus cart item qty
                minusCart(cartId, 'minus');

                // Total cart item count
                var cartCount = $(".cart_count").length - 1
                if (cartCount === 0) {
                    $(".cart_section").hide("slow");
                    $(".cart_empty_section").show("slow");
                };

                // Set cart count in navbar
                $(".cart_of_user").text("(" + cartCount + ")");
            }
        } else if (parseInt(siblings.val(), 10) > 1) {
            siblings.val(parseInt(siblings.val(), 10) - 1);
            // Get cart id
            var cartId = $(this).data('cart-id');

            // Minus cart item qty
            minusCart(cartId, 'minus');
        }
    });

    // Increament
    $(document).on('click', '.inc-btn', function (e) {
        e.preventDefault();

        var siblings = $(this).siblings('input');
        siblings.val(parseInt(siblings.val(), 10) + 1);

        // Get cart id
        var cartId = $(this).data('cart-id');

        // Plus cart item qty
        plusCart(cartId, 'plus');

    });



    /* ===============================================================
         BOOTSTRAP SELECT
      =============================================================== */
    $('.selectpicker').on('change', function () {
        $(this).closest('.dropdown').find('.filter-option-inner-inner').addClass('selected');
    });


    /* ===============================================================
         TOGGLE ALTERNATIVE BILLING ADDRESS
      =============================================================== */
    $('#alternateAddressCheckbox').on('change', function () {
        var checkboxId = '#' + $(this).attr('id').replace('Checkbox', '');
        $(checkboxId).toggleClass('d-none');
    });


    /* ===============================================================
         DISABLE UNWORKED ANCHORS
      =============================================================== */
    $('a[href="#"]').on('click', function (e) {
        e.preventDefault();
    });

});


/* ===============================================================
     COUNTRY SELECT BOX FILLING
  =============================================================== */
$.getJSON('js/countries.json', function (data) {
    $.each(data, function (key, value) {
        var selectOption = "<option value='" + value.name + "' data-dial-code='" + value.dial_code + "'>" + value.name + "</option>";
        $("select.country").append(selectOption);
    });
})