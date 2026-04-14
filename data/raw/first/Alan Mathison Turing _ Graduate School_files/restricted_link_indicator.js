/**
 * @file
 * Contains JS functionality for adding icons to document links.
 */

(function (Drupal, $, once) {
  'use strict';
  Drupal.behaviors.restricted_link_indicator = {
    attach: function (context, settings) {
      $(once('lock-icons', 'a.restricted', context)).each(function () {
        $(this).append('<span class="icon-lock" aria-hidden="true"></span>');
      });
    }
  };
}(Drupal, jQuery, once));
