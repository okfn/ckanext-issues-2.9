"use strict";

/* An user list module for display the list of users with admin or manager role
 * from a dataset organization
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
        users = res['result'].sort((a,b) => a['fullname'].toLowerCase() >= b['fullname'].toLowerCase())
        for (let user of users) {
          let userOpt = document.createElement('option')
          userOpt.value = user['id']
          userOpt.innerHTML = user['fullname']
          this.el[0].appendChild(userOpt)
        }
      })
    }
  };
});
