/**
 * @file
 * Contains JS functionality for Back To Top button.
 */

(function ($, Drupal, once) {
  'use strict';
  Drupal.behaviors.back_to_top = {
    attach: function (context, settings) {

      let offset = $(window).height() * 1.2;

      if (once('scrollBackToTop', 'body').length) {
        let $backToTopButton = $('.back-to-top');
        $(document).scroll(function () {
          if (document.body.scrollTop > offset || document.documentElement.scrollTop > offset) {
            $backToTopButton.removeClass('sr-only sr-only-focusable');
          }
          else {
            $backToTopButton.addClass('sr-only sr-only-focusable');
          }
        });
      }

      $(once('clickBackToTop', '.back-to-top', context)).click(function () {
        // Scroll to top and set focus on the first link.
        $('html, body').animate({scrollTop: 0}, 600);
        window.setTimeout(function () {
          $('#header a').not('.sr-only').first().focus();
        }, 1000);
      });

    }
  };

}(jQuery, Drupal, once));
