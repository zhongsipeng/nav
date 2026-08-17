

const raw = (typeof window !== 'undefined' && window.APP_CONFIG) || {}

export const appConfig = {
    ...raw
}

export default appConfig
