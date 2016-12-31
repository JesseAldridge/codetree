
class OrganizationSubscriptionsAPIResource(OrganizationSubscriptionResourceMixin):
    _listify_on = ['GET']
    _get_schema = OrgGetSchema
    _post_schema = OrgActionSchema
    _put_schema = OrgSubNoRequirementsSchema

    def get(self, organization_subscription_id=None, organization_id=None):
        # TODO Create wrapper for this exceptions at APIClass level
        try:
            if organization_subscription_id:
                ticket_data_types = bool_eval(self.url_string_args.get("ticket_data_types", "0"))
                data, meta = self.controller.get_item(
                    organization_subscription_id,
                    ticket_data_types=ticket_data_types)
            else:
                common_use_event('subscriptions_get_endpoint')

                self.params["organization_id"] = organization_id or current_user.organization_id
                data, meta = self.controller.get_collection(self.limit, self.offset, self.order_by,
                    self.order_dir, **self.params)
            return GigwalkAPIResponse(data=data, metadata=meta)
        except NotFound as e:
            abort(404, error_code=SubscriptionErrors.database_error,
                  error_kwargs={'errormsg': e.description})
