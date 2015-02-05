(function($) {
  $(document).ready(function() {
    $(".template-proxy-roles-settings input.textline-field").each(function() {
      $(this).autocomplete({
        source: function(request, response) {
          $.ajax({
            url: portal_url + "/@@proxy-search-users",
            dataType: "json",
            data: {
              search_term: request.term
            },
            success: function(data) {
              response(data);
            },
            error: function (xhr, ajaxOptions, thrownError) {
              alert(xhr.status);
              alert(thrownError);
            }
          });
        },
        minLength: 3
      });
    });
  });
})(jQuery);
