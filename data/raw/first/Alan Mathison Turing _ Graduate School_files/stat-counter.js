/*(function ($) {

  "use strict";
    
  var counterUp = window.counterUp["default"]; // import counterUp from "counterup2"
  
  var $counters = $(".counter");
  
  /* Start counting, do this on DOM ready or with Waypoints. 
  $counters.each(function (ignore, counter) {
      counterUp(counter, {
          duration: 1000,
          delay: 16
      });
  });
})(jQuery) */

if (window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
      var counterUp = window.counterUp["default"]; // import counterUp from "counterup2"
      var $counters = jQuery(".stat-number");

      /* Start counting, do this on DOM ready or with Waypoints. */
      $counters.each(function (ignore, counter) {
        var waypoint = new Waypoint({
          element: jQuery(this),
          handler: function () {
            counterUp(counter, {
              duration: 1000,
              delay: 16
            });
            this.destroy();
          },
          offset: 'bottom-in-view',
        });

      });
    };

