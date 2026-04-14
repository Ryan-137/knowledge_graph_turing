/**
 * @file
 * Contains JS functionality for the Slider style of Content Lists.
 */
(function (Drupal, once) {
  'use strict';

  const scrollSlider = function (sliderContainer, direction) {
    const slidesContainer = sliderContainer.querySelector('.content-list-items');
    const firstSlide = sliderContainer.querySelector('.content-list-item');
    const slideGapInPixels = parseFloat(window.getComputedStyle(slidesContainer).getPropertyValue('column-gap'));
    const scrollAmount = firstSlide.offsetWidth + slideGapInPixels;
    slidesContainer.scrollBy({ left: direction * scrollAmount, behavior: 'smooth'});
  };

  const findFirstVisibleItemInSlider = function (sliderContainer) {
    const slidesContainer = sliderContainer.querySelector('.content-list-items');
    const items = sliderContainer.querySelectorAll('.content-list-item');
    const slidesContainerRect = slidesContainer.getBoundingClientRect();
    for (const item of items) {
      const rect = item.getBoundingClientRect();
      if (rect.left >= slidesContainerRect.left && rect.right <= slidesContainerRect.right) {
        return item;
      }
    }
    return null;
  };

  const setFocusToFirstVisibleLinkedTitleInSlider = function (sliderContainer) {
    const firstVisibleItem = findFirstVisibleItemInSlider(sliderContainer);
    if (firstVisibleItem) {
      const firstTitleLink = firstVisibleItem.querySelector('.field--name-title a');
      if (firstTitleLink) {
        firstTitleLink.focus();
      }
    }
  };

  const setOverflowClassesOnSlider = function (slidesContainer) {
    const isScrolledLeft = slidesContainer.scrollLeft > 0;
    const isScrolledRight = slidesContainer.scrollLeft + slidesContainer.clientWidth < slidesContainer.scrollWidth;

    const sliderContainer = slidesContainer.closest('.content-list-slider');
    const prevButton = sliderContainer.querySelector('.btn-prev');
    const nextButton = sliderContainer.querySelector('.btn-next');
    const skipLink = sliderContainer.querySelector('.skip-link');

    if (isScrolledLeft) {
      if (!sliderContainer.classList.contains('overflow-left')) {
        sliderContainer.classList.add('overflow-left');
      }
      prevButton.disabled = false;
      if (skipLink) {
        skipLink.style.display = 'inline';
      }
    }
    else {
      if (sliderContainer.classList.contains('overflow-left')) {
        sliderContainer.classList.remove('overflow-left');
      }
      prevButton.disabled = true;
      if (skipLink) {
        skipLink.style.display = 'none';
      }
    }

    if (isScrolledRight) {
      if (!sliderContainer.classList.contains('overflow-right')) {
        sliderContainer.classList.add('overflow-right');
      }
      nextButton.disabled = false;
    }
    else {
      if (sliderContainer.classList.contains('overflow-right')) {
        sliderContainer.classList.remove('overflow-right');
      }
      nextButton.disabled = true;
    }
  };

  Drupal.behaviors.content_list_slider = {
    attach: function (context, settings) {
      once('content-list-slider', '.content-list-slider').forEach(sliderContainer => {
        sliderContainer.querySelector('.btn-next').addEventListener('click', () => {
          scrollSlider(sliderContainer, 1);
        });
        sliderContainer.querySelector('.btn-prev').addEventListener('click', () => {
          scrollSlider(sliderContainer , -1);
        });

        // Remove the skip link if the slider doesn't contain any title links.
        // There's nothing for a user to tab focus to in a slider like this,
        // so we don't need the skip link.
        const skipLink = sliderContainer.querySelector('.skip-link');
        const slidesHaveTitleLinks = sliderContainer.querySelectorAll('.field--name-title a').length > 0;
        if (!slidesHaveTitleLinks) {
          skipLink.remove();
        }
        else {
          skipLink.addEventListener('click', e => {
            e.preventDefault();
            setFocusToFirstVisibleLinkedTitleInSlider(sliderContainer);
          });
        }

        const slidesContainer = sliderContainer.querySelector('.content-list-items');
        setOverflowClassesOnSlider(slidesContainer);
        slidesContainer.addEventListener('scroll', () => {
          setOverflowClassesOnSlider(slidesContainer);
        });
      });
    }
  };
}(Drupal, once));
