/** Feature flag for the "Look up by address" affordance on the predict form.
 *
 * Default OFF. Flip by setting `NEXT_PUBLIC_ADDRESS_LOOKUP_ENABLED=true`
 * in the environment when starting the Next.js dev/build.
 */
export function isAddressLookupEnabled(): boolean {
  return process.env.NEXT_PUBLIC_ADDRESS_LOOKUP_ENABLED === "true";
}
