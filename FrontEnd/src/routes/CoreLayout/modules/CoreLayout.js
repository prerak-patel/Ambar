import { titles, stateValueExtractor, urls, constants, analytics } from 'utils'
import 'whatwg-fetch'

const CHANGE_FIELD = 'CORE.CHANGE_FIELD'
const HANDLE_ERROR = 'CORE.HANDLE_ERROR'
const CLOSE_NOTIFICATION = 'CORE.CLOSE_NOTIFICATION'
const SHOW_INFO = 'CORE.SHOW_INFO'

export const loadConfig = () => {
    return (dispatch, getState) => {
        dispatch(startLoadingIndicator())

        getApiUrl()
            .then(apiUrl => dispatch(changeField('urls', urls(apiUrl))))
            .then(() => getCrawlerJsonTemplate())
            .then(crawlerJsonTemplate => dispatch(changeField('crawlerJsonTemplate', crawlerJsonTemplate)))
            .then(() => getLocalizationsJson())
            .then(localizations => dispatch(changeField('localizations', JSON.parse(localizations))))
            .then(() => {
                const urls = stateValueExtractor.getUrls(getState())
                return getWebApiInfo(urls.ambarWebApiGetInfo())
            })
            .then(apiInfo => {             
                const urls = stateValueExtractor.getUrls(getState())   

                dispatch(changeField('mode', apiInfo.mode))
                dispatch(changeField('version', apiInfo.version))
                dispatch(changeField('integrations', apiInfo.integrations))
                dispatch(changeField('auth', apiInfo.auth))                
                dispatch(changeField('lang', apiInfo.uiLang))   
                dispatch(changeField('preserveOriginals', apiInfo.preserveOriginals))   

                analytics(apiInfo.analytics.token)
                analytics().register({ apiUrl: urls.apiHost })
                analytics().register({ mode: apiInfo.mode })

            })
            .then(() => dispatch(stopLoadingIndicator()))
            .catch(error => {
                console.error(`Failed to start. Error: ${error}`)
                dispatch(handleError(error))
            })
    }
}

export const setPageTitle = (title) => {
    return (dispatch, getState) => {        
        titles.setPageTitle(title)        
    }
}

const startLoadingIndicator = () => {
    return (dispatch, getState) => {
        dispatch(changeField('fetching', true))
    }
}

const stopLoadingIndicator = () => {
    return (dispatch, getState) => {
        dispatch(changeField('fetching', false))
    }
}

const getApiUrl = () => new Promise((resolve, reject) => {
    fetch('apiUrl.txt', {
        method: 'GET'
    })
        .then(resp => resolve(resp.text()))
        .catch(err => reject(err))
})

const getCrawlerJsonTemplate = () => new Promise((resolve, reject) => {
    fetch('crawlerJsonTemplate.json', {
        method: 'GET'
    })
        .then(resp => resolve(resp.text()))
        .catch(err => reject(err))
})

const getLocalizationsJson = () => new Promise((resolve, reject) => {
    fetch('localizations.json', {
        method: 'GET'
    })
        .then(resp => resolve(resp.text()))
        .catch(err => reject(err))
})

const getWebApiInfo = (url) => new Promise((resolve, reject) => {
    fetch(url, {
        method: 'GET'
    })
        .then(resp => resolve(resp.json()))
        .catch(err => reject(err))
})

export function showInfo(message) {
    return {
        type: SHOW_INFO,
        message
    }
}

export function handleError(error, showErrorMessage = false) {    
    if (error.constructor === Response) {
        error = `Response ${error.status} ${error.statusText} at ${error.url}`
    }    
    analytics().event('ERROR', { description: error ? error.toString() : 'no info' })
    console.error(error)

    return {
        type: HANDLE_ERROR,
        error,
        showErrorMessage
    }
}

export function closeNotification() {
    return {
        type: CLOSE_NOTIFICATION
    }
}

const changeField = (fieldName, value) => {
    return {
        type: CHANGE_FIELD,
        fieldName,
        value
    }
}

const ACTION_HANDLERS = {
    [CHANGE_FIELD]: (state, action) => {
        const newState = { ...state }
        newState[action.fieldName] = action.value

        return newState
    },
    [HANDLE_ERROR]: (state, action) => {
        return ({ ...state, isNotificationOpen: true, fetching: false, notificationMessage: action.showErrorMessage ? action.error : constants.errorMessage, notificationReason: 'error' })
    },
    [SHOW_INFO]: (state, action) => {
        return ({ ...state, isNotificationOpen: true, fetching: false, notificationMessage: action.message, notificationReason: 'info' })
    },
    [CLOSE_NOTIFICATION]: (state, action) => {
        return ({ ...state, isNotificationOpen: false })
    }    
}

const initialState = {
    urls: {},
    crawlerJsonTemplate: '',
    localizations: {},
    lang: 'en',
    integrations: {},
    mode: 'ce',
    version: '0.0',
    fetching: true,
    isNotificationOpen: false,
    notificationMessage: '',
    notificationReason: 'error',
    auth: 'basic'
}

export default function coreLayoutReducer(state = initialState, action) {
    const handler = ACTION_HANDLERS[action.type]
    return handler ? handler(state, action) : state
}