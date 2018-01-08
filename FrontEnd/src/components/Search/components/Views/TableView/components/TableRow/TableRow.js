import React, { Component } from 'react'

import FileDownloadIcon from 'material-ui/svg-icons/file/file-download'
import TextPreviewIcon from 'material-ui/svg-icons/action/subject'
import ImagePreviewIcon from 'material-ui/svg-icons/image/image'
import DeleteIcon from 'material-ui/svg-icons/action/delete'
import IconButton from 'material-ui/IconButton'
import UndoIcon from 'material-ui/svg-icons/content/undo'

import { files } from 'utils/'
import moment from 'moment'
import {
    Table,
    TableBody,
    TableHeader,
    TableHeaderColumn,
    TableRow,
    TableRowColumn,
} from 'material-ui/Table'
import { FileAvatar, TagsInput, ClickableFilePath, AuthorLabel, FileSizeLabel, UpdatedDateTimeLabel } from 'components/BasicComponents'

import classes from './TableRow.scss'

const getFormattedTime = (date) => {
    return moment(date).format('DD.MM.YYYY HH:mm')
}

class TableRowResult extends Component {

    render() {
        const {
            hit: {
                fetching: fetching,
            meta: meta,
            content: content,
            sha256: sha256,
            tags: tags,
            file_id: fileId,
            isHidden: isHidden,
            hidden_mark: hidden_mark
            },
            allTags,
            searchQuery,
            thumbnailUri,
            downloadUri,
            performSearchByAuthor,
            performSearchByPathToFile,
            toggleImagePreview,
            addTagToFile,
            removeTagFromFile,
            performSearchByTag,
            hideFile,
            showFile,
            openTextPreview,
            localization,
            preserveOriginals
        } = this.props

        const contentHighlight = content && content.highlight && content.highlight.text ? content.highlight.text : undefined

        return (
            <TableRow>
                <TableRowColumn style={{ width: '60px', paddingLeft: '15px', paddingRight: '5px' }}>
                    <FileAvatar meta={meta} searchFunction={performSearchByPathToFile} />
                </TableRowColumn>
                <TableRowColumn title={meta.full_name} style={{ width: '35%', whiteSpace: 'normal', wordWrap: 'break-word' }}>
                    <b>{meta.short_name}</b>
                    <ClickableFilePath meta={meta} performSearchByPathToFile={performSearchByPathToFile} />
                </TableRowColumn>
                <TableRowColumn title={files.formatFileSize(content.size)}><FileSizeLabel content={content} searchQuery={searchQuery} /></TableRowColumn>
                <TableRowColumn style={{ overflow: 'visible' }} >
                    <TagsInput
                        tags={tags}
                        onAddTag={(tagType, tagName) => addTagToFile(fileId, tagType, tagName)}
                        onRemoveTag={(tagType, tagName) => removeTagFromFile(fileId, tagType, tagName)}
                        performSearchByTag={performSearchByTag}
                        suggestions={allTags.map(t => t.name)}
                    />
                </TableRowColumn>
                <TableRowColumn title={content.author}><AuthorLabel content={content} performSearchByAuthor={performSearchByAuthor} /></TableRowColumn>
                <TableRowColumn title={getFormattedTime(meta.updated_datetime)}>
                    <UpdatedDateTimeLabel meta={meta} searchQuery={searchQuery} formatFunc={getFormattedTime} />
                </TableRowColumn>
                <TableRowColumn style={{ width: '220px' }}>
                    {preserveOriginals && <IconButton onTouchTap={() => { window.open(downloadUri) }}
                        title={localization.searchPage.downloadDescriptionLabel}>
                        <FileDownloadIcon color='#00bcd4' hoverColor='#80deea' />
                    </IconButton>}
                    <IconButton
                        disabled={!files.doesFileContainText(meta)}
                        onTouchTap={() => openTextPreview(fileId)}
                        title={localization.searchPage.previewDescriptionLabel}
                    >
                        <TextPreviewIcon color='#00bcd4' hoverColor='#80deea' />
                    </IconButton>
                    <IconButton
                        disabled={!(contentHighlight && content.thumb_available)}
                        onTouchTap={() => {
                            toggleImagePreview(thumbnailUri)
                        }}
                        title={localization.searchPage.imagePreviewLabel}>
                        <ImagePreviewIcon color='#00bcd4' hoverColor='#80deea' />
                    </IconButton>
                    {!hidden_mark && <IconButton onTouchTap={() => hideFile(fileId)} title={localization.searchPage.removeLabel}>
                        <DeleteIcon color='#00bcd4' hoverColor='#80deea' />
                    </IconButton>}
                    {(isHidden || hidden_mark) && <IconButton onTouchTap={() => showFile(fileId)} title={localization.searchPage.restoreLabel}>
                        <UndoIcon color='#00bcd4' hoverColor='#80deea' />
                    </IconButton>}
                </TableRowColumn>
            </TableRow>
        )
    }
}


TableRowResult.propTypes = {
    hit: React.PropTypes.object.isRequired,
    allTags: React.PropTypes.array.isRequired,
    searchQuery: React.PropTypes.string.isRequired,
    thumbnailUri: React.PropTypes.string.isRequired,
    downloadUri: React.PropTypes.string.isRequired,
    performSearchByAuthor: React.PropTypes.func.isRequired,
    performSearchByPathToFile: React.PropTypes.func.isRequired,
    toggleImagePreview: React.PropTypes.func.isRequired,
    addTagToFile: React.PropTypes.func.isRequired,
    removeTagFromFile: React.PropTypes.func.isRequired,
    performSearchByTag: React.PropTypes.func.isRequired,
    hideFile: React.PropTypes.func.isRequired,
    showFile: React.PropTypes.func.isRequired,
    openTextPreview: React.PropTypes.func.isRequired,
    preserveOriginals: React.PropTypes.bool.isRequired
}

export default TableRowResult




