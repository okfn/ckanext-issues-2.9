"use strict";

/* An auto-complete module for select and input elements that can pull in
 * a list of terms from an API endpoint (provided using data-module-source).
 *
 * source   - A url pointing to an API autocomplete endpoint.
 * interval - The interval between requests in milliseconds (default: 1000).
 * items    - The max number of items to display (default: 10)
 * tags     - Boolean attribute if true will create a tag input.
 * key      - A string of the key you want to be the form value to end up on
 *            from the ajax returned results
 * label    - A string of the label you want to appear within the dropdown for
 *            returned results
 *
 * Examples
 *
 *   // <input name="tags" data-module="autocomplete" data-module-source="http://" />
 *
 */

ckan.module('list-users-assign-api', function (jQuery, _) {
  return {
    /* Options for the module */
    options: {
      organization_id: ''
    },

    /* Sets up the module, binding methods, creating elements etc. Called
     * internally by ckan.module.initialize();
     *
     * Returns nothing.
     */
    initialize: function () {
      jQuery.proxyAll(this, /_on/, /format/);
      this.getUsers();
    },

    /* Sets up the auto complete plugin.
     *
     * Returns nothing.
     */
    getUsers: function () {
      let users = []
      $.ajax('/api/3/action/organization_users?organization_id=' + this.options.organization_id).then((res) => {
        console.log(this.el)
        users = res['result'].sort((a,b) => a.toLowerCase() >= b.toLowerCase())
        for (let user of users) {
          let userOpt = document.createElement('option')
          userOpt.value = user['id']
          userOpt.innerHTML = user['name']
          this.el[0].appendChild(userOpt)
        }
      })
    }
  };
});
